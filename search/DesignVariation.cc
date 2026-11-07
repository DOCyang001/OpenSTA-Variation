// OpenSTA, Static Timing Analyzer
// Copyright (c) 2026, Parallax Software, Inc.

#include "DesignVariation.hh"

#include <algorithm>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <locale>
#include <sstream>
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
#include "Liberty.hh"
#include "Search.hh"
#include "Variables.hh"
#include "PocvMode.hh"
#include "Crpr.hh"

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

// V24 integration added by DOCyang001/OpenSTA-private.
// Serialize OpenSTA graph moments into the two standalone algorithms' schema.
// The compatibility text is an interchange file, not a PrimeTime report.
namespace sta {
namespace {
struct VariationRow {
  std::string point;
  std::string cell;
  char transition;
  double mean;
  double sigma;
  double corner;
};

std::vector<VariationRow>
variationRows(const Path *path, const StaState *sta)
{
  std::vector<VariationRow> rows;
  if (!path)
    return rows;
  PathExpanded expanded(path, true, sta);
  for (size_t i = 0; i < expanded.size(); ++i) {
    const Path *current = expanded.path(i);
    const Pin *pin = current->pin(sta);
    const Network *network = sta->network();
    const Instance *instance = network->instance(pin);
    const LibertyCell *cell = network->libertyCell(instance);
    if (!cell)
      continue; // Ports have no cell arc; their fixed offsets are in the budget.
    const std::string point = network->pathName(pin);
    if (point.find_first_of(" \t\r\n()") != std::string::npos
        || cell->name().find_first_of(" \t\r\n()") != std::string::npos)
      sta->report()->error(1620, "V24 interchange cannot encode whitespace or parentheses in pin/cell names.");
    double mean = 0.0;
    double sigma = 0.0;
    double corner = 0.0;
    if (i > 0) {
      const Path *previous = expanded.path(i - 1);
      mean = current->arrival().mean() - previous->arrival().mean();
      TimingArc *arc = current->prevArc(sta);
      Edge *edge = current->prevEdge(sta);
      if (arc && edge) {
        // Do not subtract statistical arrivals: their variances are correlated.
        const Delay delay = sta->search()->deratedDelay(
            previous->vertex(sta), arc, edge, current->isClock(sta),
            current->minMax(sta), current->dcalcAnalysisPtIndex(sta),
            current->sdc(sta));
        if (delay.meanShift() != 0.0F || delay.skewness() != 0.0F)
          sta->report()->error(1621, "V24 requires symmetric normal arc moments.");
        if (network->instance(previous->pin(sta)) == instance) {
          sigma = delay.stdDev();
          corner = mean + delayAsFloat(delay, current->minMax(sta), sta) - delay.mean();
        }
        else if (delay.stdDev() != 0.0F)
          sta->report()->error(1622, "V24 models fixed net delays; statistical net delay is unsupported.");
      }
    }
    if (!std::isfinite(mean) || !std::isfinite(sigma) || !std::isfinite(corner))
      sta->report()->error(1623, "Non-finite timing moment in V24 export.");
    if (sigma < 0.0)
      sta->report()->error(1624, "Negative arc standard deviation in V24 export.");
    // For a fixed delay, Corner equals Mean.
    if (sigma == 0.0)
      corner = mean;
    rows.push_back({point, cell->name(),
                    current->transition(sta) == RiseFall::rise() ? 'r' : 'f',
                    mean, sigma, corner});
  }
  return rows;
}

double variationRowSum(const std::vector<VariationRow> &rows,
                       const std::string &through = "")
{
  double sum = 0.0;
  for (const auto &row : rows) {
    sum += row.mean;
    if (!through.empty() && row.point == through)
      break;
  }
  return sum;
}

void variationWriteRows(std::ostream &out,
                        const std::vector<VariationRow> &rows,
                        double scale)
{
  for (const auto &row : rows)
    out << "  " << row.point << " (" << row.cell << ") 0 0 "
        << row.mean / scale << ' ' << row.sigma / scale << ' '
        << row.corner / scale << ' ' << row.corner / scale
        << " 0 " << row.transition << '\n';
}
} // namespace

void writeDesignVariationTiming(PathEndSeq *path_ends,
                                const char *filename)
{
  Sta *sta = Sta::sta();
  if (!path_ends || path_ends->empty())
    sta->report()->error(1625, "No paths supplied for variation analysis.");
  if (!sta->variables()->pocvEnabled()
      || sta->variables()->pocvMode() != PocvMode::normal)
    sta->report()->error(1626, "V24 requires enabled normal POCV with characterized arc sigma.");
  const double scale = sta->units()->timeUnit()->scale();
  std::ostringstream out;
  out.imbue(std::locale::classic());
  out << std::scientific << std::setprecision(17);
  out << "# OpenSTA V24 interchange; time values use the current OpenSTA time unit.\n"
      << "# Fixed constraint/edge/CRPR offsets are aggregated in clock uncertainty.\n"
      << "# Setup-check sigma is fixed, matching the standalone V24 model.\n";
  for (PathEnd *end : *path_ends) {
    if (!end || end->isUnconstrained() || !end->path()
        || end->checkGenericRole(sta) != TimingRole::setup()
        || end->isLatchCheck())
      sta->report()->error(1627, "V24 supports constrained flip-flop setup paths only; hold/latch paths are unsupported.");
    const Path *path = end->path();
    const Path *capture = end->targetClkPath();
    PathExpanded expanded(path, true, sta);
    const Path *start = expanded.startPath();
    const Instance *launch = sta->network()->instance(start->pin(sta));
    const LibertyCell *launch_cell = sta->network()->libertyCell(launch);
    if (!launch_cell || !launch_cell->isSequential())
      sta->report()->error(1628, "V24 native export currently requires register-to-register setup paths.");
    const auto data_rows = variationRows(path, sta);
    const auto capture_rows = variationRows(capture, sta);
    std::string common;
    Crpr correction;
    Pin *common_pin = nullptr;
    if (capture)
      sta->search()->checkCrpr()->checkCrpr(path, capture, correction, common_pin);
    if (common_pin) {
      const std::string name = sta->network()->pathName(common_pin);
      const auto has = [&name](const auto &rows) {
        return std::any_of(rows.begin(), rows.end(),
                           [&name](const auto &row) { return row.point == name; });
      };
      if (has(data_rows) && has(capture_rows))
        common = name;
    }
    const double slack = end->slack(sta).mean();
    if (!std::isfinite(slack))
      sta->report()->error(1629, "Non-finite nominal setup slack.");
    double fixed = slack + variationRowSum(data_rows) - variationRowSum(capture_rows);
    if (!common.empty())
      fixed -= variationRowSum(data_rows, common) - variationRowSum(capture_rows, common);
    out << "\n  Startpoint: " << sta->network()->pathName(launch)
        << " (flip-flop)\n  Endpoint: " << pinName(path->pin(sta), sta)
        << " (flip-flop)\n  Path Group: OpenSTA\n  Path Type: max\n";
    if (!common.empty())
      out << "  Last common pin: " << common << '\n';
    out << "  Point Fanout Cap Mean Sensit Corner Value Path\n";
    variationWriteRows(out, data_rows, scale);
    out << "  data arrival time " << path->arrival().mean() / scale << '\n';
    variationWriteRows(out, capture_rows, scale);
    out << "  clock uncertainty " << fixed / scale << '\n'
        << "  data required time " << (path->arrival().mean() + slack) / scale << '\n';
  }
  // Validate the whole collection before creating/truncating the destination.
  std::ofstream file(filename);
  if (!file)
    sta->report()->error(1630, "Cannot open V24 interchange file.");
  file << out.str();
  file.close();
  if (!file)
    sta->report()->error(1631, "Failed writing V24 interchange file.");
}
} // namespace sta

