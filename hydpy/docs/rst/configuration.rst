
.. _configuration:

Configuration Tools
===================


The `conf` subpackage provides some hard coded files that configure some
aspects of *HydPy*.

The binary |numpy| file `a_coefficients_explicit_lobatto_sequence.npy`
provides the Runge-Kutta coefficients required by models subclassed from
|ModelELS|.  ToDo: use a platfrom-independent file format.

The XML schema file `config.xsd` is automatically generated based on its
template file `config.xsdt`, and defines the required and possible
contents of XML configuration files to be executed with function |exec_xml|.
