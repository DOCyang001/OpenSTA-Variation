# OpenSTA, Static Timing Analyzer

namespace eval sta {

define_cmd_args "report_design_variation" \
  {path_ends [-samples count] [-sigma_limit limit] [-seed seed]\
              [-bottlenecks count]}

proc report_design_variation { args } {
  parse_key_args "report_design_variation" args \
    keys {-samples -sigma_limit -seed -bottlenecks} flags {}
  check_argc_eq1 "report_design_variation" $args

  set samples 1000
  if { [info exists keys(-samples)] } {
    set samples $keys(-samples)
    check_positive_integer "-samples" $samples
  }
  set sigma_limit 6.0
  if { [info exists keys(-sigma_limit)] } {
    set sigma_limit $keys(-sigma_limit)
    check_float "-sigma_limit" $sigma_limit
    if { $sigma_limit <= 0.0 } {
      sta_error 1613 "-sigma_limit must be positive."
    }
  }
  set seed 1
  if { [info exists keys(-seed)] } {
    set seed $keys(-seed)
    check_positive_integer "-seed" $seed
  }
  set bottlenecks 10
  if { [info exists keys(-bottlenecks)] } {
    set bottlenecks $keys(-bottlenecks)
    check_positive_integer "-bottlenecks" $bottlenecks
  }

  report_design_variation_cmd [lindex $args 0] $samples $sigma_limit \
    $seed $bottlenecks
}

}
