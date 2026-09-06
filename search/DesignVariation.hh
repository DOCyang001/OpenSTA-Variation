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

} // namespace sta
