# OpenSTA, Static Timing Analyzer
# V24 extension of the existing report_design_variation interface.
namespace eval sta {

define_cmd_args "report_design_variation" \
  {path_ends [-samples count] [-sigma_limit target_sigma] [-seed seed]
   [-bottlenecks count] [-tail_samples count] [-output_dir directory]
   [-python executable] [-script_dir directory]}

define_cmd_args "report_variation_bottleneck" \
  {path_ends [-output_dir directory] [-python executable] [-script_dir directory]
   [-clock_paths include|exclude] [-exclude_VT labels]
   [-variation_threshold value] [-sigma_threshold value] [-max_violators count]}

proc variation_backend {kind paths option_list} {
  array set opts $option_list
  set python python3
  if {[info exists opts(-python)]} { set python $opts(-python) }
  set candidates {}
  if {[info exists opts(-script_dir)]} {
    lappend candidates $opts(-script_dir)
  } elseif {[info exists ::env(STA_VARIATION_SCRIPTS)]} {
    lappend candidates $::env(STA_VARIATION_SCRIPTS)
  } else {
    set bin [file dirname [info nameofexecutable]]
    lappend candidates [file join $bin share OpenSTA variation]
    lappend candidates [file join $bin .. share OpenSTA variation]
  }
  set driver ""
  foreach candidate $candidates {
    set file [file join $candidate opensta_variation.py]
    if {[file isfile $file]} { set driver [file normalize $file]; break }
  }
  if {$driver eq ""} {
    error "V24 backend not found; use -script_dir or STA_VARIATION_SCRIPTS."
  }
  set output [file join [pwd] "${kind}_variation_[pid]_[clock clicks]"]
  if {[info exists opts(-output_dir)]} { set output $opts(-output_dir) }
  set output [file normalize $output]
  if {[file exists $output]} {
    if {![file isdirectory $output]} { error "Output path must be a directory." }
    if {[llength [glob -nocomplain -directory $output * .*]] > 2} {
      error "Refusing nonempty output directory: $output"
    }
    # glob .* also returns . and .. on some Tcl versions; use explicit filtering.
    foreach entry [glob -nocomplain -directory $output * .*] {
      if {[file tail $entry] ni {. ..}} {
        error "Refusing nonempty output directory: $output"
      }
    }
  }
  # List expansion preserves paths with spaces and never invokes a shell.
  set command [list $python -X utf8 $driver --kind $kind --output-dir $output]
  foreach {key flag} {
    -samples --samples -sigma_limit --sigma -seed --seed
    -bottlenecks --bottlenecks -tail_samples --tail-samples
    -clock_paths --clock-paths -exclude_VT --exclude-vt
    -variation_threshold --variation-threshold -sigma_threshold --sigma-threshold
    -max_violators --max-violators
  } {
    if {[info exists opts($key)]} { lappend command $flag $opts($key) }
  }
  # Check dependencies before exporting or creating the output directory.
  exec $python -X utf8 $driver --check-dependencies 2>@1
  file mkdir $output
  set input [file join $output timing.rpt]
  write_design_variation_timing_cmd $paths $input
  lappend command --input $input
  set result [exec {*}$command 2>@1]
  puts $result
  return $output
}

proc report_design_variation {args} {
  parse_key_args "report_design_variation" args \
    keys {-samples -sigma_limit -seed -bottlenecks -tail_samples -output_dir -python -script_dir} flags {}
  check_argc_eq1 "report_design_variation" $args
  foreach {key default} {-samples 1000 -sigma_limit 6.0 -seed 1 -bottlenecks 10} {
    if {![info exists keys($key)]} { set keys($key) $default }
  }
  foreach key {-samples -tail_samples -seed -bottlenecks} {
    if {[info exists keys($key)]} { check_positive_integer $key $keys($key) }
  }
  if {$keys(-samples) < 2 || ([info exists keys(-tail_samples)] && $keys(-tail_samples) < 2)} {
    error "V24 requires at least two ordinary and tail samples."
  }
  check_float "-sigma_limit" $keys(-sigma_limit)
  if {![expr {$keys(-sigma_limit) > 0.0 && $keys(-sigma_limit) <= 8.0}]} {
    error "-sigma_limit must be finite and in (0, 8]; it is the target quantile, not a sampling cutoff."
  }
  return [variation_backend design [lindex $args 0] [array get keys]]
}

proc report_variation_bottleneck {args} {
  parse_key_args "report_variation_bottleneck" args \
    keys {-output_dir -python -script_dir -clock_paths -exclude_VT -variation_threshold -sigma_threshold -max_violators} flags {}
  check_argc_eq1 "report_variation_bottleneck" $args
  if {[info exists keys(-clock_paths)] && $keys(-clock_paths) ni {include exclude}} {
    error "-clock_paths must be include or exclude."
  }
  foreach key {-variation_threshold -sigma_threshold} {
    if {[info exists keys($key)]} {
      check_float $key $keys($key)
      if {![expr {$keys($key) >= 0.0 && $keys($key) < Inf}]} {
        error "$key must be finite and nonnegative."
      }
    }
  }
  if {[info exists keys(-max_violators)]} {
    check_positive_integer "-max_violators" $keys(-max_violators)
  }
  return [variation_backend bottleneck [lindex $args 0] [array get keys]]
}
}

