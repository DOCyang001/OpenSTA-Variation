%{
#include "search/DesignVariation.hh"
%}

%inline %{
void
report_design_variation_cmd(PathEndSeq *path_ends,
                            int sample_count,
                            float sigma_limit,
                            unsigned seed,
                            int bottleneck_count)
{
  sta::reportDesignVariation(path_ends, sample_count, sigma_limit, seed,
                             bottleneck_count);
}
%}
