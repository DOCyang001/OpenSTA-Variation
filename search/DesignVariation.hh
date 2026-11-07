// OpenSTA, Static Timing Analyzer
// Copyright (c) 2026, Parallax Software, Inc.

#pragma once

#include "SearchClass.hh"

namespace sta {

void
reportDesignVariation(PathEndSeq *path_ends,
                       int sample_count,
                       float sigma_limit,
                       unsigned seed,
                       int bottleneck_count);

// Export native normal-POCV setup paths for the V24 analysis backend.
void writeDesignVariationTiming(PathEndSeq *path_ends, const char *filename);

} // namespace sta

