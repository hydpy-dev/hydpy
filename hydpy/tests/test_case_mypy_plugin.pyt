from hydpy import prepare_model

prepare_model("exch_branch_hbv69")
model = prepare_model("exch_branch_hbv96")

reveal_type(prepare_model("exch_branch_hbv69"))
model = prepare_model("exch_branch_hbv96")
reveal_type(model)

reveal_type(model.nodenames)

reveal_type(model.calc_outputs)
model.calc_outputs()
reveal_type(model.calc_outputs_v1)
reveal_type(model.calc_outputs_v2)
ga = prepare_model("ga_garto")
reveal_type(ga.return_conductivity_v1)
reveal_type(ga.return_conductivity(1, 2))

reveal_type(model.parameters)
reveal_type(model.sequences)

control = model.parameters.control
reveal_type(control)
fluxes = model.sequences.fluxes
reveal_type(fluxes)
reveal_type(control.pars)
reveal_type(fluxes.pars)
reveal_type(control.seqs)
reveal_type(fluxes.seqs)
reveal_type(control.vars)
reveal_type(fluxes.vars)
xpoints = control.xpoints
reveal_type(xpoints)
outputs = fluxes.outputs
reveal_type(outputs)
reveal_type(xpoints.NDIM)
reveal_type(outputs.NDIM)
reveal_type(xpoints.subpars)  # model specific?
reveal_type(outputs.subseqs)  # model specific?
reveal_type(xpoints.subvars)  # model specific?
reveal_type(outputs.subvars)  # model specific?
reveal_type(control.zpoints)
reveal_type(fluxes.inputs)
control.xpoints = 1.0
reveal_type(control.xpoints)
fluxes.outputs = 1.0
reveal_type(fluxes.outputs)
