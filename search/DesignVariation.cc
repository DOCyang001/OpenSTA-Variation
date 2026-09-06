// OpenSTA, Static Timing Analyzer
// Copyright (c) 2026, Parallax Software, Inc.

#include "DesignVariation.hh"

#include <algorithm>
#include <cmath>
#include <limits>
#include <random>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

#include "Format.hh"
#include "Graph.hh"
#include "Network.hh"
#include "Path.hh"
#include "PathEnd.hh"
#include "PathExpanded.hh"
#include "Report.hh"
#include "Sta.hh"
#include "TimingArc.hh"
#include "TimingRole.hh"
#include "Units.hh"

namespace sta {

namespace {

struct RandomKey
{
  const void *object1;
  const void *object2;

  bool operator==(const RandomKey &other) const
  {
    return object1 == other.object1 && object2 == other.object2;
  }
};

struct RandomKeyHash
{
  size_t operator()(const RandomKey &key) const
  {
    const size_t h1 = std::hash<const void*>{}(key.object1);
    const size_t h2 = std::hash<const void*>{}(key.object2);
    return h1 ^ (h2 + 0x9e3779b9U + (h1 << 6) + (h1 >> 2));
  }
};

struct Contribution
{
  RandomKey key;
  std::string name;
  double sigma;
  double sign;
};

struct PathSample
{
  std::string endpoint;
  double nominal_slack;
  std::vector<Contribution> contributions;
};

struct ArcStats
{
  std::string name;
  double speed_sum = 0.0;
  double speed_sum2 = 0.0;
  double value_slack_sum = 0.0;
};

std::string
pinName(const Pin *pin,
        const StaState *sta)
{
  return pin ? sta->network()->pathName(pin) : "?";
}

void
collectPathContributions(const Path *path,
                         double sign,
                         const StaState *sta,
                         std::vector<Contribution> &contributions)
{
  if (path == nullptr)
    return;

  PathExpanded expanded(path, sta);
  for (size_t index = expanded.startIndex() + 1;
       index < expanded.size(); index++) {
    const Path *current = expanded.path(index);
    const Path *previous = expanded.path(index - 1);
    TimingArc *arc = current->prevArc(sta);
    Edge *edge = current->prevEdge(sta);
    if (arc == nullptr || edge == nullptr || previous == nullptr)
      continue;

    Delay increment = delayDiff(current->arrival(), previous->arrival(), sta);
    const double sigma = std::max(0.0, static_cast<double>(increment.stdDev()));
    if (sigma == 0.0)
      continue;

    contributions.push_back({
        {edge, arc},
        sta::format("{} -> {}", pinName(previous->pin(sta), sta),
                    pinName(current->pin(sta), sta)),
        sigma,
        sign});
  }
}

double
nominalSlack(PathEnd *end,
             const StaState *sta)
{
  return static_cast<double>(delayAsFloat(end->slack(sta),
                                          end->pathEarlyLate(sta),
                                          sta));
}

std::string
formatTime(double value,
           const StaState *sta)
{
  return sta->units()->timeUnit()->asString(static_cast<float>(value), 4);
}

} // namespace

void
reportDesignVariation(PathEndSeq *path_ends,
                       int sample_count,
                       float sigma_limit,
                       unsigned seed,
                       int bottleneck_count)
{
  Sta *sta = Sta::sta();
  Report *report = sta->report();
  if (path_ends == nullptr || path_ends->empty()) {
    report->reportLine("Design variation: no paths.");
    return;
  }
  if (sample_count < 1)
    report->error(1610, "sample count must be positive.");
  if (sigma_limit <= 0.0F)
    report->error(1611, "sigma limit must be positive.");
  if (bottleneck_count < 1)
    report->error(1612, "bottleneck count must be positive.");

  std::vector<PathSample> paths;
  std::unordered_map<RandomKey, ArcStats, RandomKeyHash> arc_stats;
  paths.reserve(path_ends->size());

  for (PathEnd *end : *path_ends) {
    if (end == nullptr || end->isUnconstrained() || end->path() == nullptr)
      continue;

    const TimingRole *role = end->checkGenericRole(sta);
    const bool setup = role == TimingRole::setup();
    PathSample sample{
        pinName(end->path()->pin(sta), sta),
        nominalSlack(end, sta),
        {}};
    collectPathContributions(end->path(), setup ? -1.0 : 1.0, sta,
                             sample.contributions);
    collectPathContributions(end->targetClkPath(), setup ? 1.0 : -1.0, sta,
                             sample.contributions);

    const double margin_sigma = end->margin(sta).stdDev();
    if (margin_sigma > 0.0) {
      sample.contributions.push_back({
          {end, nullptr},
          sta::format("{} check margin", sample.endpoint),
          margin_sigma,
          -1.0});
    }

    for (const Contribution &contribution : sample.contributions) {
      ArcStats &stats = arc_stats[contribution.key];
      stats.name = contribution.name;
    }
    paths.push_back(std::move(sample));
  }

  if (paths.empty()) {
    report->reportLine("Design variation: no constrained paths.");
    return;
  }

  std::mt19937 generator(seed);
  std::normal_distribution<double> normal(0.0, 1.0);
  std::unordered_map<RandomKey, double, RandomKeyHash> speed;
  speed.reserve(arc_stats.size());

  double design_sum = 0.0;
  double design_sum2 = 0.0;
  double design_min = std::numeric_limits<double>::infinity();
  double design_max = -std::numeric_limits<double>::infinity();
  int pass_count = 0;

  for (int sample_index = 0; sample_index < sample_count; sample_index++) {
    speed.clear();
    for (auto &entry : arc_stats) {
      double value;
      do {
        value = normal(generator);
      } while (std::abs(value) > sigma_limit);
      speed.emplace(entry.first, value);
      ArcStats &stats = entry.second;
      stats.speed_sum += value;
      stats.speed_sum2 += value * value;
    }

    std::unordered_map<std::string, double> endpoint_min;
    for (const PathSample &path : paths) {
      double slack = path.nominal_slack;
      for (const Contribution &contribution : path.contributions)
        slack += contribution.sign * contribution.sigma
                 * speed[contribution.key];
      auto endpoint = endpoint_min.find(path.endpoint);
      if (endpoint == endpoint_min.end())
        endpoint_min.emplace(path.endpoint, slack);
      else
        endpoint->second = std::min(endpoint->second, slack);
    }

    double design_slack = std::numeric_limits<double>::infinity();
    for (const auto &endpoint : endpoint_min)
      design_slack = std::min(design_slack, endpoint.second);
    if (design_slack >= 0.0)
      pass_count++;
    design_sum += design_slack;
    design_sum2 += design_slack * design_slack;
    design_min = std::min(design_min, design_slack);
    design_max = std::max(design_max, design_slack);

    for (const auto &entry : speed) {
      ArcStats &stats = arc_stats[entry.first];
      stats.value_slack_sum += entry.second * design_slack;
    }
  }

  const double count = sample_count;
  const double design_mean = design_sum / count;
  const double design_variance = std::max(0.0,
      design_sum2 / count - design_mean * design_mean);
  const double design_stddev = std::sqrt(design_variance);

  struct Bottleneck { std::string name; double correlation; };
  std::vector<Bottleneck> bottlenecks;
  for (const auto &entry : arc_stats) {
    const ArcStats &stats = entry.second;
    const double mean = stats.speed_sum / count;
    const double variance = std::max(0.0,
        stats.speed_sum2 / count - mean * mean);
    const double stddev = std::sqrt(variance);
    const double covariance = stats.value_slack_sum / count
                              - mean * design_mean;
    const double correlation = stddev > 0.0 && design_stddev > 0.0
        ? covariance / (stddev * design_stddev)
        : 0.0;
    bottlenecks.push_back({stats.name, correlation});
  }
  std::sort(bottlenecks.begin(), bottlenecks.end(),
            [] (const Bottleneck &left, const Bottleneck &right) {
              return std::abs(left.correlation) > std::abs(right.correlation);
            });

  report->reportLine("Design variation report");
  report->reportLine(sta::format("  paths      : {}", paths.size()));
  report->reportLine(sta::format("  samples    : {}", sample_count));
  report->reportLine(sta::format("  sigma limit: {:.3f}", sigma_limit));
  report->reportLine(sta::format("  seed       : {}", seed));
  report->reportLine(sta::format("  yield      : {:.6f} ({}/{})",
                                 static_cast<double>(pass_count) / count,
                                 pass_count, sample_count));
  report->reportLine(sta::format("  failure    : {:.6f}",
                                 1.0 - static_cast<double>(pass_count) / count));
  report->reportLine(sta::format("  design slack mean/stddev: {} / {}",
                                 formatTime(design_mean, sta),
                                 formatTime(design_stddev, sta)));
  report->reportLine(sta::format("  design slack min/max     : {} / {}",
                                 formatTime(design_min, sta),
                                 formatTime(design_max, sta)));
  report->reportLine("  yield bottlenecks (arc vs design slack correlation):");
  const int count_to_report = std::min<int>(bottleneck_count,
                                            bottlenecks.size());
  for (int index = 0; index < count_to_report; index++)
    report->reportLine(sta::format("    {:2d}. {:<40} {:.6f}",
                                   index + 1,
                                   bottlenecks[index].name,
                                   bottlenecks[index].correlation));
}

} // namespace sta
