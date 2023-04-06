# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# imports...
# ...from HydPy
from hydpy.core import modeltools
from hydpy.cythons import modelutils

# ...from grxjland
from hydpy.models.snow import snow_inputs
from hydpy.models.snow import snow_fluxes
from hydpy.models.snow import snow_control
from hydpy.models.snow import snow_fixed
from hydpy.models.snow import snow_states
from hydpy.models.snow import snow_derived
from hydpy.models.snow import snow_logs


class Calc_PLayer_V1(modeltools.Method):
    """Calculate the precipitation as a function of altitude for all snow layers.
    Above 4000 m the precipitation does not change anymore.

    Basic equations:
        .. math:: PLayer = \begin{cases}
            P + exp \left( \left( ZLayers - Z \right) * GradP \right) &|\ ZLayers <=
            ZThreshold
            \\
            P + exp \left( \left( ZThreshold - Z \right) * GradP \right) &|\ Z <=
            ZThreshold
            \\
            P
            \end{cases}

    Todo Nichts zu Grenzwert 4000 in originaler Veröffentlichung gefunden. Aber
            Ergebnisse stimmen mit airGR überein

    Examples:

        >>> from hydpy.models.snow import *
        >>> from hydpy import pub
        >>> pub.options.reprdigits = 6
        >>> parameterstep('1d')
        >>> nsnowlayers(5)
        >>> inputs.p(10.)

        Elevation of ZLayers with mean value lower than 4000.:

        >>> z(3999)
        >>> hypsodata(numpy.linspace(2999, 4999, 101))
        >>> derived.zlayers.update()
        >>> derived.zlayers
        zlayers(3199.0, 3599.0, 3999.0, 4399.0, 4799.0)

        >>> model.calc_player_v1()

        >>> fluxes.player
        player(7.881562, 9.28617, 10.941098, 10.945585, 10.945585)

        Elevation of ZLayers with mean value greater than 4000.:

        >>> z(4001)
        >>> hypsodata(numpy.linspace(3001, 5001, 101))
        >>> derived.zlayers.update()
        >>> derived.zlayers
        zlayers(3201.0, 3601.0, 4001.0, 4401.0, 4801.0)

        >>> model.calc_player_v1()

        >>> fluxes.player
        player(7.882977, 9.287837, 10.943062, 10.943062, 10.943062)

        Elevation of ZLayers with mean value of exactly 4000.:

        >>> z(4000)
        >>> hypsodata(numpy.linspace(3000, 5000, 101))
        >>> derived.zlayers.update()
        >>> derived.zlayers
        zlayers(3200.0, 3600.0, 4000.0, 4400.0, 4800.0)

        >>> model.calc_player_v1()

        >>> fluxes.player
        player(7.882977, 9.287837, 10.943062, 10.943062, 10.943062)
    """

    CONTROLPARAMETERS = (
        snow_control.NSnowLayers,
        snow_control.Z,
    )

    FIXEDPARAMETERS = (
        snow_fixed.GradP,
        snow_fixed.ZThreshold,
    )

    DERIVEDPARAMETERS = (snow_derived.ZLayers,)

    REQUIREDSEQUENCES = (snow_inputs.P,)
    RESULTSEQUENCES = (snow_fluxes.PLayer,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fix = model.parameters.fixed.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess

        # calculate mean precipitation to scale
        d_meanplayer = 0.0
        for k in range(con.nsnowlayers):
            if der.zlayers[k] <= fix.zthreshold:
                flu.player[k] = inp.p * modelutils.exp(
                    fix.gradp * (der.zlayers[k] - con.z)
                )
            elif con.z <= fix.zthreshold:
                flu.player[k] = inp.p * modelutils.exp(
                    fix.gradp * (fix.zthreshold - con.z)
                )
            else:
                flu.player[k] = inp.p
            d_meanplayer = d_meanplayer + flu.player[k] / con.nsnowlayers
        # scale precipitation, that the mean of yone precipitation is equal to the
        # subbasin precipitation
        if d_meanplayer > 0.0:
            for k in range(con.nsnowlayers):
                flu.player[k] = flu.player[k] / d_meanplayer * inp.p


class Calc_TLayer_V1(modeltools.Method):
    """Calculate daily mean temperature for each snow layer in dependence of
    elevation taking into account the temperature-altitude gradient.

    Basic equation:
        :math:`TLayer = T + (Z - ZLayers) * GradTMean / 100`


    Examples:

        >>> from hydpy.models.snow import *
        >>> from hydpy import pub
        >>> ret = pub.options.reprdigits(6)
        >>> parameterstep('1d')
        >>> nsnowlayers(5)
        >>> z(1636)
        >>> derived.zlayers(1052., 1389., 1626., 1822., 2013.)

        Define temperature gradient for each day in year

        # todo: woher? Zusammenhang?
        >>> gradtmean(0.434, 0.434, 0.435, 0.436, 0.437, 0.439, 0.44, 0.441, 0.442,
        ...     0.444, 0.445, 0.446, 0.448, 0.45, 0.451, 0.453, 0.455, 0.456, 0.458,
        ...     0.46, 0.462, 0.464, 0.466, 0.468, 0.47, 0.472, 0.474, 0.476, 0.478,
        ...     0.48, 0.483, 0.485, 0.487, 0.489, 0.492, 0.494, 0.496, 0.498, 0.501,
        ...     0.503, 0.505, 0.508, 0.51, 0.512, 0.515, 0.517, 0.519, 0.522, 0.524,
        ...     0.526, 0.528, 0.53, 0.533, 0.535, 0.537, 0.539, 0.541, 0.543, 0.545,
        ...     0.546, 0.547, 0.549, 0.551, 0.553, 0.555, 0.557, 0.559, 0.56, 0.562,
        ...     0.564, 0.566, 0.567, 0.569, 0.57, 0.572, 0.573, 0.575, 0.576, 0.577,
        ...     0.579, 0.58, 0.581, 0.582, 0.583, 0.584, 0.585, 0.586, 0.587, 0.588,
        ...     0.589, 0.59, 0.591, 0.591, 0.592, 0.593, 0.593, 0.594, 0.595, 0.595,
        ...     0.596, 0.596, 0.597, 0.597, 0.597, 0.598, 0.598, 0.598, 0.599, 0.599,
        ...     0.599, 0.599, 0.6, 0.6, 0.6, 0.6, 0.6, 0.601, 0.601, 0.601, 0.601,
        ...     0.601, 0.601, 0.601, 0.601, 0.601, 0.601, 0.601, 0.601, 0.601, 0.601,
        ...     0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602,
        ...     0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602,
        ...     0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602,
        ...     0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602,
        ...     0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.601, 0.601, 0.601,
        ...     0.601, 0.601, 0.601, 0.6, 0.6, 0.6, 0.6, 0.599, 0.599, 0.599, 0.598,
        ...     0.598, 0.598, 0.597, 0.597, 0.597, 0.596, 0.596, 0.595, 0.595, 0.594,
        ...     0.594, 0.593, 0.593, 0.592, 0.592, 0.591, 0.59, 0.59, 0.589, 0.588,
        ...     0.588, 0.587, 0.586, 0.586, 0.585, 0.584, 0.583, 0.583, 0.582, 0.581,
        ...     0.58, 0.579, 0.578, 0.578, 0.577, 0.576, 0.575, 0.574, 0.573, 0.572,
        ...     0.571, 0.57, 0.569, 0.569, 0.568, 0.567, 0.566, 0.565, 0.564, 0.563,
        ...     0.562, 0.561, 0.56, 0.558, 0.557, 0.556, 0.555, 0.554, 0.553, 0.552,
        ...     0.551, 0.55, 0.549, 0.548, 0.546, 0.545, 0.544, 0.543, 0.542, 0.541,
        ...     0.54, 0.538, 0.537, 0.536, 0.535, 0.533, 0.532, 0.531, 0.53, 0.528,
        ...     0.527, 0.526, 0.525, 0.523, 0.522, 0.521, 0.519, 0.518, 0.517, 0.515,
        ...     0.514, 0.512, 0.511, 0.51, 0.508, 0.507, 0.505, 0.504, 0.502, 0.501,
        ...     0.499, 0.498, 0.496, 0.495, 0.493, 0.492, 0.49, 0.489, 0.487, 0.485,
        ...     0.484, 0.482, 0.481, 0.479, 0.478, 0.476, 0.475, 0.473, 0.471, 0.47,
        ...     0.468, 0.467, 0.465, 0.464, 0.462, 0.461, 0.459, 0.458, 0.456, 0.455,
        ...     0.454, 0.452, 0.451, 0.45, 0.448, 0.447, 0.446, 0.445, 0.443, 0.442,
        ...     0.441, 0.44, 0.439, 0.438, 0.437, 0.436, 0.435, 0.434, 0.434, 0.433,
        ...     0.432, 0.431, 0.431, 0.43, 0.43, 0.429, 0.429, 0.429, 0.428, 0.428,
        ...     0.428, 0.428, 0.428, 0.428, 0.428, 0.428, 0.429, 0.429, 0.429, 0.43,
        ...     0.43, 0.431, 0.431, 0.432, 0.433)
        >>> inputs.t = -1.60835

        Now we prepare a |DOY| object, that assumes that the first, second,
        and third simulation time steps are first, second and third day of year,
        respectively:

        # todo: hier pub.timegrids verwenden?

        >>> derived.doy.shape = 3
        >>> derived.doy = 0, 1, 2
        >>> model.idx_sim = 1

        >>> model.calc_tlayer_v1()
        >>> fluxes.tlayer
        tlayer(0.92621, -0.53637, -1.56495, -2.41559, -3.24453)

        Second simulation step

        >>> inputs.t = -2.44165
        >>> model.calc_tlayer_v1()
        >>> fluxes.tlayer
        tlayer(0.09291, -1.36967, -2.39825, -3.24889, -4.07783)

        Third simulation step

        >>> inputs.t = -10.41945
        >>> model.calc_tlayer_v1()
        >>> fluxes.tlayer
        tlayer(-7.88489, -9.34747, -10.37605, -11.22669, -12.05563)

    """

    CONTROLPARAMETERS = (
        snow_control.NSnowLayers,
        snow_control.Z,
        snow_control.GradTMean,
    )

    DERIVEDPARAMETERS = (
        snow_derived.ZLayers,
        snow_derived.DOY,
    )

    REQUIREDSEQUENCES = (snow_inputs.T,)
    RESULTSEQUENCES = (snow_fluxes.TLayer,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess

        for k in range(con.nsnowlayers):
            flu.tlayer[k] = (
                inp.t
                + (con.z - der.zlayers[k])
                * con.gradtmean[der.doy[model.idx_sim]]
                / 100.0
            )


class Calc_TLayer_V2(modeltools.Method):

    # todo: Berechnet was anderes als calc_tlayerv1 sollte es dann nicht auch
    #  anders heißen. Wird nirgendwo verwendet???? Formeln auseinander ziehen
    """Calculate daily mean, minimum, maximum air temperature for each snow layer in
    dependence of elevation.

        Basic equation:


    Examples:

        >>> from hydpy.models.snow import *
        >>> from hydpy import pub
        >>> ret = pub.options.reprdigits(6)
        >>> parameterstep('1d')
        >>> nsnowlayers(5)
        >>> z(1636)
        >>> derived.zlayers(1052., 1389., 1626., 1822., 2013.)

        Define temperature gradients for each day in year

        >>> gradtmean(0.434, 0.434, 0.435, 0.436, 0.437, 0.439, 0.44, 0.441, 0.442,
        ...     0.444, 0.445, 0.446, 0.448, 0.45, 0.451, 0.453, 0.455, 0.456, 0.458,
        ...     0.46, 0.462, 0.464, 0.466, 0.468, 0.47, 0.472, 0.474, 0.476, 0.478,
        ...     0.48, 0.483, 0.485, 0.487, 0.489, 0.492, 0.494, 0.496, 0.498, 0.501,
        ...     0.503, 0.505, 0.508, 0.51, 0.512, 0.515, 0.517, 0.519, 0.522, 0.524,
        ...     0.526, 0.528, 0.53, 0.533, 0.535, 0.537, 0.539, 0.541, 0.543, 0.545,
        ...     0.546, 0.547, 0.549, 0.551, 0.553, 0.555, 0.557, 0.559, 0.56, 0.562,
        ...     0.564, 0.566, 0.567, 0.569, 0.57, 0.572, 0.573, 0.575, 0.576, 0.577,
        ...     0.579, 0.58, 0.581, 0.582, 0.583, 0.584, 0.585, 0.586, 0.587, 0.588,
        ...     0.589, 0.59, 0.591, 0.591, 0.592, 0.593, 0.593, 0.594, 0.595, 0.595,
        ...     0.596, 0.596, 0.597, 0.597, 0.597, 0.598, 0.598, 0.598, 0.599, 0.599,
        ...     0.599, 0.599, 0.6, 0.6, 0.6, 0.6, 0.6, 0.601, 0.601, 0.601, 0.601,
        ...     0.601, 0.601, 0.601, 0.601, 0.601, 0.601, 0.601, 0.601, 0.601, 0.601,
        ...     0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602,
        ...     0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602,
        ...     0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602,
        ...     0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602,
        ...     0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.601, 0.601, 0.601,
        ...     0.601, 0.601, 0.601, 0.6, 0.6, 0.6, 0.6, 0.599, 0.599, 0.599, 0.598,
        ...     0.598, 0.598, 0.597, 0.597, 0.597, 0.596, 0.596, 0.595, 0.595, 0.594,
        ...     0.594, 0.593, 0.593, 0.592, 0.592, 0.591, 0.59, 0.59, 0.589, 0.588,
        ...     0.588, 0.587, 0.586, 0.586, 0.585, 0.584, 0.583, 0.583, 0.582, 0.581,
        ...     0.58, 0.579, 0.578, 0.578, 0.577, 0.576, 0.575, 0.574, 0.573, 0.572,
        ...     0.571, 0.57, 0.569, 0.569, 0.568, 0.567, 0.566, 0.565, 0.564, 0.563,
        ...     0.562, 0.561, 0.56, 0.558, 0.557, 0.556, 0.555, 0.554, 0.553, 0.552,
        ...     0.551, 0.55, 0.549, 0.548, 0.546, 0.545, 0.544, 0.543, 0.542, 0.541,
        ...     0.54, 0.538, 0.537, 0.536, 0.535, 0.533, 0.532, 0.531, 0.53, 0.528,
        ...     0.527, 0.526, 0.525, 0.523, 0.522, 0.521, 0.519, 0.518, 0.517, 0.515,
        ...     0.514, 0.512, 0.511, 0.51, 0.508, 0.507, 0.505, 0.504, 0.502, 0.501,
        ...     0.499, 0.498, 0.496, 0.495, 0.493, 0.492, 0.49, 0.489, 0.487, 0.485,
        ...     0.484, 0.482, 0.481, 0.479, 0.478, 0.476, 0.475, 0.473, 0.471, 0.47,
        ...     0.468, 0.467, 0.465, 0.464, 0.462, 0.461, 0.459, 0.458, 0.456, 0.455,
        ...     0.454, 0.452, 0.451, 0.45, 0.448, 0.447, 0.446, 0.445, 0.443, 0.442,
        ...     0.441, 0.44, 0.439, 0.438, 0.437, 0.436, 0.435, 0.434, 0.434, 0.433,
        ...     0.432, 0.431, 0.431, 0.43, 0.43, 0.429, 0.429, 0.429, 0.428, 0.428,
        ...     0.428, 0.428, 0.428, 0.428, 0.428, 0.428, 0.429, 0.429, 0.429, 0.43,
        ...     0.43, 0.431, 0.431, 0.432, 0.433)
        >>> gradtmin(0.366, 0.366, 0.367, 0.367, 0.367, 0.367, 0.367, 0.368, 0.368,
        ...     0.368, 0.368, 0.368, 0.369, 0.369, 0.369, 0.37, 0.37, 0.37, 0.371,
        ...     0.371, 0.371, 0.372, 0.372, 0.373, 0.373, 0.374, 0.374, 0.375, 0.375,
        ...     0.376, 0.376, 0.377, 0.377, 0.378, 0.379, 0.379, 0.38, 0.381, 0.381,
        ...     0.382, 0.383, 0.384, 0.384, 0.385, 0.386, 0.387, 0.387, 0.388, 0.389,
        ...     0.39, 0.391, 0.392, 0.393, 0.393, 0.394, 0.395, 0.396, 0.397, 0.398,
        ...     0.399, 0.399, 0.4, 0.401, 0.402, 0.403, 0.404, 0.405, 0.406, 0.406,
        ...     0.407, 0.408, 0.409, 0.41, 0.411, 0.412, 0.413, 0.414, 0.415, 0.416,
        ...     0.417,  0.417, 0.418, 0.419, 0.42, 0.421, 0.422, 0.422, 0.423, 0.424,
        ...     0.425, 0.425, 0.426, 0.427, 0.427, 0.428, 0.429, 0.429, 0.43, 0.431,
        ...     0.431, 0.432, 0.432, 0.433, 0.433, 0.434, 0.434, 0.435, 0.435, 0.436,
        ...     0.436, 0.436, 0.437, 0.437, 0.437, 0.438, 0.438, 0.438, 0.438, 0.439,
        ...     0.439, 0.439, 0.439, 0.439, 0.439, 0.44, 0.44, 0.44, 0.44, 0.44, 0.44,
        ...     0.44, 0.44, 0.44, 0.44, 0.44, 0.44, 0.44, 0.44, 0.44, 0.44, 0.44, 0.44,
        ...     0.44, 0.44, 0.44, 0.44, 0.44, 0.439, 0.439, 0.439, 0.439, 0.439, 0.439,
        ...     0.439, 0.439, 0.439, 0.439, 0.438, 0.438, 0.438, 0.438, 0.438, 0.438,
        ...     0.438, 0.438, 0.438, 0.437, 0.437, 0.437, 0.437, 0.437, 0.437, 0.437,
        ...     0.436, 0.436, 0.436, 0.436, 0.436, 0.436, 0.436, 0.435, 0.435, 0.435,
        ...     0.435, 0.435, 0.434, 0.434, 0.434, 0.434, 0.434, 0.433, 0.433, 0.433,
        ...     0.433, 0.432, 0.432, 0.432, 0.432, 0.431, 0.431, 0.431, 0.43, 0.43,
        ...     0.43, 0.429, 0.429, 0.428, 0.428, 0.428, 0.427, 0.427, 0.426, 0.426,
        ...     0.425, 0.425, 0.424, 0.424, 0.423, 0.423, 0.422, 0.421, 0.421, 0.42,
        ...     0.42, 0.419, 0.418, 0.418, 0.417, 0.416, 0.415, 0.415, 0.414, 0.413,
        ...     0.413, 0.412, 0.411, 0.41, 0.409, 0.409, 0.408, 0.407, 0.406, 0.405,
        ...     0.405, 0.404, 0.403, 0.402, 0.401, 0.401, 0.4, 0.399, 0.398, 0.397,
        ...     0.396, 0.396, 0.395, 0.394, 0.393, 0.392, 0.391, 0.391, 0.39, 0.389,
        ...     0.388, 0.388, 0.387, 0.386, 0.385, 0.385, 0.384, 0.383, 0.383, 0.382,
        ...     0.381, 0.381, 0.38, 0.379, 0.379, 0.378, 0.377, 0.377, 0.376, 0.376,
        ...     0.375, 0.375, 0.374, 0.374, 0.373, 0.373, 0.372, 0.372, 0.372, 0.371,
        ...     0.371, 0.371, 0.37, 0.37, 0.37, 0.369, 0.369, 0.369, 0.368, 0.368,
        ...     0.368, 0.368, 0.368, 0.367, 0.367, 0.367, 0.367, 0.367, 0.367, 0.366,
        ...     0.366, 0.366, 0.366, 0.366, 0.366, 0.366, 0.366, 0.366, 0.366, 0.365,
        ...     0.365, 0.365, 0.365, 0.365, 0.365, 0.365, 0.365, 0.365, 0.365, 0.365,
        ...     0.365, 0.365, 0.365, 0.365, 0.365, 0.365, 0.365, 0.365, 0.365, 0.365,
        ...     0.365, 0.365, 0.365, 0.365, 0.365, 0.365, 0.365, 0.365, 0.365, 0.365,
        ...     0.365, 0.365, 0.365, 0.365, 0.365, 0.366, 0.366, 0.366, 0.366, 0.366,
        ...     0.366, 0.366, 0.366)
        >>> gradtmax(0.498, 0.5, 0.501, 0.503, 0.504, 0.506, 0.508, 0.51, 0.512,
        ...     0.514, 0.517, 0.519, 0.522, 0.525, 0.527, 0.53, 0.533, 0.537, 0.54,
        ...     0.543, 0.547, 0.55, 0.554, 0.558, 0.561, 0.565, 0.569, 0.573, 0.577,
        ...     0.582, 0.586, 0.59, 0.594, 0.599, 0.603, 0.607, 0.612, 0.616, 0.621,
        ...     0.625, 0.63, 0.634, 0.639, 0.643, 0.648, 0.652, 0.657, 0.661, 0.666,
        ...     0.67, 0.674, 0.679, 0.683, 0.687, 0.691, 0.695, 0.699, 0.703, 0.707,
        ...     0.709, 0.711, 0.715, 0.718, 0.722, 0.726, 0.729, 0.732, 0.736, 0.739,
        ...     0.742, 0.745, 0.748, 0.75, 0.753, 0.756, 0.758, 0.761, 0.763, 0.765,
        ...     0.767, 0.769, 0.771, 0.773, 0.774, 0.776, 0.777, 0.779, 0.78, 0.781,
        ...     0.782, 0.783, 0.784, 0.785, 0.785, 0.786, 0.787, 0.787, 0.787, 0.788,
        ...     0.788, 0.788, 0.788, 0.788, 0.788, 0.788, 0.788, 0.787, 0.787, 0.787,
        ...     0.786, 0.786, 0.785, 0.785, 0.784, 0.784, 0.783, 0.783, 0.782, 0.781,
        ...     0.781, 0.78, 0.779, 0.778, 0.778, 0.777, 0.776, 0.775, 0.775, 0.774,
        ...     0.773, 0.772, 0.772, 0.771, 0.77, 0.77, 0.769, 0.768, 0.768, 0.767,
        ...     0.767, 0.766, 0.766, 0.765, 0.765, 0.764, 0.764, 0.764, 0.763, 0.763,
        ...     0.763, 0.762, 0.762, 0.762, 0.762, 0.762, 0.762, 0.762, 0.761, 0.761,
        ...     0.761, 0.761, 0.761, 0.762, 0.762, 0.762, 0.762, 0.762, 0.762, 0.762,
        ...     0.762, 0.763, 0.763, 0.763, 0.763, 0.763, 0.764, 0.764, 0.764, 0.764,
        ...     0.764, 0.765, 0.765, 0.765, 0.765, 0.765, 0.766, 0.766, 0.766, 0.766,
        ...     0.766, 0.766, 0.766, 0.766, 0.766, 0.767, 0.767, 0.767, 0.766, 0.766,
        ...     0.766, 0.766, 0.766, 0.766, 0.766, 0.765, 0.765, 0.765, 0.765, 0.764,
        ...     0.764, 0.764, 0.763, 0.763, 0.762, 0.762, 0.761, 0.761, 0.76, 0.76,
        ...     0.759, 0.758, 0.758, 0.757, 0.756, 0.755, 0.754, 0.754, 0.753, 0.752,
        ...     0.751, 0.75, 0.749, 0.748, 0.747, 0.746, 0.745, 0.744, 0.743, 0.742,
        ...     0.741, 0.74, 0.738, 0.737, 0.736, 0.735, 0.734, 0.732, 0.731, 0.73,
        ...     0.728, 0.727, 0.725, 0.724, 0.723, 0.721, 0.72, 0.718, 0.717, 0.715,
        ...     0.713, 0.712, 0.71, 0.709, 0.707, 0.705, 0.703, 0.702, 0.7, 0.698,
        ...     0.696, 0.694, 0.692, 0.69, 0.688, 0.686, 0.684, 0.682, 0.68, 0.678,
        ...     0.676, 0.674, 0.671, 0.669, 0.667, 0.664, 0.662, 0.659, 0.657, 0.654,
        ...     0.652, 0.649, 0.647, 0.644, 0.641, 0.639, 0.636, 0.633, 0.63, 0.628,
        ...     0.625, 0.622, 0.619, 0.616, 0.613, 0.61, 0.607, 0.604, 0.601, 0.598,
        ...     0.595, 0.592, 0.589, 0.586, 0.583, 0.58, 0.577, 0.574, 0.571, 0.568,
        ...     0.565, 0.562, 0.559, 0.556, 0.553, 0.55, 0.547, 0.544, 0.542, 0.539,
        ...     0.536, 0.533, 0.531, 0.528, 0.526, 0.523, 0.521, 0.519, 0.517, 0.515,
        ...     0.513, 0.511, 0.509, 0.507, 0.505, 0.504, 0.502, 0.501, 0.5, 0.498,
        ...     0.497, 0.496, 0.496, 0.495, 0.494, 0.494, 0.494, 0.493, 0.493, 0.493,
        ...     0.493, 0.494, 0.494, 0.495, 0.495, 0.496, 0.497)
        >>> inputs.t = -1.60835
        >>> inputs.tmin = -3.2
        >>> inputs.tmax = 2.2

        Now we prepare a |DOY| object, that assumes that the first, second,
        and third simulation time steps are first, second and third day of year,
        respectively:

        >>> derived.doy.shape = 3
        >>> derived.doy = 0, 1, 2
        >>> model.idx_sim = 1

        >>> model.calc_tlayer_v2()
        >>> fluxes.tlayer
        tlayer(0.92621, -0.53637, -1.56495, -2.41559, -3.24453)
        >>> fluxes.tminlayer
        tminlayer(-1.06256, -2.29598, -3.1634, -3.88076, -4.57982)
        >>> fluxes.tmaxlayer
        tmaxlayer(5.12, 3.435, 2.25, 1.27, 0.315)

        Second simulation step

        >>> inputs.t = -2.44165
        >>> inputs.tmin = -5.1
        >>> inputs.tmax = 0.3
        >>> model.calc_tlayer_v2()
        >>> fluxes.tlayer
        tlayer(0.09291, -1.36967, -2.39825, -3.24889, -4.07783)
        >>> fluxes.tminlayer
        tminlayer(-2.96256, -4.19598, -5.0634, -5.78076, -6.47982)
        >>> fluxes.tmaxlayer
        tmaxlayer(3.22, 1.535, 0.35, -0.63, -1.585)

        Third simulation step

        >>> inputs.t = -10.41945
        >>> inputs.tmin = -16.3
        >>> inputs.tmax = -5.3
        >>> model.calc_tlayer_v2()
        >>> fluxes.tlayer
        tlayer(-7.88489, -9.34747, -10.37605, -11.22669, -12.05563)
        >>> fluxes.tminlayer
        tminlayer(-14.16256, -15.39598, -16.2634, -16.98076, -17.67982)
        >>> fluxes.tmaxlayer
        tmaxlayer(-2.38, -4.065, -5.25, -6.23, -7.185)

    """

    CONTROLPARAMETERS = (
        snow_control.NSnowLayers,
        snow_control.Z,
        snow_control.GradTMean,
        snow_control.GradTMax,
        snow_control.GradTMin,
    )

    DERIVEDPARAMETERS = (
        snow_derived.ZLayers,
        snow_derived.DOY,
    )

    REQUIREDSEQUENCES = (
        snow_inputs.T,
        snow_inputs.TMin,
        snow_inputs.TMax,
    )
    RESULTSEQUENCES = (
        snow_fluxes.TLayer,
        snow_fluxes.TMinLayer,
        snow_fluxes.TMaxLayer,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess

        # todo: Warum hier fabs?

        for k in range(con.nsnowlayers):
            flu.tlayer[k] = (
                inp.t
                + (con.z - der.zlayers[k])
                * modelutils.fabs(con.gradtmean[der.doy[model.idx_sim]])
                / 100.0
            )
            flu.tminlayer[k] = (
                inp.tmin
                + (con.z - der.zlayers[k])
                * modelutils.fabs(con.gradtmin[der.doy[model.idx_sim]])
                / 100.0
            )
            flu.tmaxlayer[k] = (
                inp.tmax
                + (con.z - der.zlayers[k])
                * modelutils.fabs(con.gradtmax[der.doy[model.idx_sim]])
                / 100.0
            )


class Calc_FracSolidPrec_V1(modeltools.Method):
    """Calculate solid precipitation fraction [-] for each snow layer.
    Above 3°C all precipiation is rain, below -1 °C all precipitation is snow,
    in between it is linear decreasing

        Basic equation:


    Examples:

        >>> from hydpy.models.snow import *
        >>> from hydpy import pub
        >>> ret = pub.options.reprdigits(6)
        >>> parameterstep('1d')
        >>> nsnowlayers(9)
        >>> fluxes.tlayer = -3.0, -3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 3.0
        >>> fluxes.player = 0.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 0.0

        >>> model.calc_fracsolidprec_v1()
        >>> fluxes.solidfraction
        solidfraction(1.0, 1.0, 1.0, 1.0, 0.75, 0.5, 0.25, 0.0, 0.0)
        >>> fluxes.psnowlayer
        psnowlayer(0.0, 5.0, 5.0, 5.0, 3.75, 2.5, 1.25, 0.0, 0.0)
        >>> fluxes.prainlayer
        prainlayer(0.0, 0.0, 0.0, 0.0, 1.25, 2.5, 3.75, 5.0, 0.0)

    """

    CONTROLPARAMETERS = (snow_control.NSnowLayers,)

    REQUIREDSEQUENCES = (
        snow_fluxes.TLayer,
        snow_fluxes.PLayer,
    )
    RESULTSEQUENCES = (
        snow_fluxes.SolidFraction,
        snow_fluxes.PSnowLayer,
        snow_fluxes.PRainLayer,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess

        for k in range(con.nsnowlayers):
            flu.solidfraction[k] = min(
                1, max(0, (3.0 - flu.tlayer[k]) / 4.0)
            )
            flu.psnowlayer[k] = flu.solidfraction[k] * flu.player[k]
            flu.prainlayer[k] = (1.0 - flu.solidfraction[k]) * flu.player[k]


class Calc_FracSolidPrec_V2(modeltools.Method):

    # Todo: Wird nicht verwendet. Kann eigentlich mit Version1 zusammengefasst werden
    """Calculate solid precipitation fraction [/] for each snow layer.

        Basic equation:


    Examples:

        >>> from hydpy.models.snow import *
        >>> from hydpy import pub
        >>> ret = pub.options.reprdigits(6)
        >>> parameterstep('1d')
        >>> nsnowlayers(5)
        >>> z(1000)
        >>> fluxes.tlayer = 0.92621, -0.53637, -1.56495, -2.41559, -3.24453
        >>> fluxes.tminlayer = -1.06256, -2.29598, -3.1634, -3.88076, -4.57982
        >>> fluxes.tmaxlayer =  5.12, 3.435, 2.25, 1.27, 0.315
        >>> fluxes.player = 5.656033, 6.494091, 7.156799, 7.755659, 8.387418
        >>> model.calc_fracsolidprec_v2()
        >>> fluxes.solidfraction
        solidfraction(0.171864, 0.400626, 0.584365, 0.753434, 0.935646)
        >>> fluxes.psnowlayer
        psnowlayer(0.972069, 2.601702, 4.182181, 5.843381, 7.847656)
        >>> fluxes.prainlayer
        prainlayer(4.683964, 3.892389, 2.974618, 1.912278, 0.539762)

        #todo: Macht doch gar keinen Sinn

        >>> z(1499)
        >>> model.calc_fracsolidprec_v2()
        >>> fluxes.solidfraction
        solidfraction(0.171864, 0.400626, 0.584365, 0.753434, 0.935646)
        >>> fluxes.psnowlayer
        psnowlayer(0.972069, 2.601702, 4.182181, 5.843381, 7.847656)
        >>> fluxes.prainlayer
        prainlayer(4.683964, 3.892389, 2.974618, 1.912278, 0.539762)

        >>> z(1500)
        >>> model.calc_fracsolidprec_v2()
        >>> fluxes.solidfraction
        solidfraction(0.518447, 0.884092, 1.0, 1.0, 1.0)
        >>> fluxes.psnowlayer
        psnowlayer(2.932356, 5.741377, 7.156799, 7.755659, 8.387418)
        >>> fluxes.prainlayer
        prainlayer(2.723677, 0.752714, 0.0, 0.0, 0.0)

    """

    CONTROLPARAMETERS = (
        snow_control.NSnowLayers,
        snow_control.Z,
    )

    REQUIREDSEQUENCES = (
        snow_fluxes.TLayer,
        snow_fluxes.PLayer,
        snow_fluxes.TMinLayer,
        snow_fluxes.TMaxLayer,
    )
    RESULTSEQUENCES = (
        snow_fluxes.SolidFraction,
        snow_fluxes.PSnowLayer,
        snow_fluxes.PRainLayer,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess

        for k in range(con.nsnowlayers):
            if con.z < 1500.0:
                flu.solidfraction[k] = min(
                    1,
                    max(
                        0,
                        1.0 - flu.tmaxlayer[k] / (flu.tmaxlayer[k] - flu.tminlayer[k]),
                    ),
                )
            else:
                flu.solidfraction[k] = min(
                    1, max(0, 1.0 - (flu.tlayer[k] + 1.0) / (3.0 + 1.0))
                )
            flu.psnowlayer[k] = flu.solidfraction[k] * flu.player[k]
            flu.prainlayer[k] = (1.0 - flu.solidfraction[k]) * flu.player[k]


class Calc_G_V1(modeltools.Method):
    """Calculate snow for each snow layer.

        Basic equations:


    Examples:

        >>> from hydpy.models.snow import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> simulationstep('1d')
        >>> nsnowlayers(5)
        >>> fluxes.psnowlayer = (0.07273111, 0.086444894, 0.09857770, 0.10418780,
        ...                      0.11285966)
        >>> states.g = 1., 0., 0., 0., 0.
        >>> model.calc_g_v1()
        >>> states.g
        g(1.072731, 0.086445, 0.098578, 0.104188, 0.11286)

    """

    CONTROLPARAMETERS = (
        snow_control.NSnowLayers,
    )

    REQUIREDSEQUENCES = (
        snow_fluxes.PSnowLayer,
    )
    UPDATEDSEQUENCES = (
        snow_states.G,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess

        for k in range(con.nsnowlayers):
            sta.g[k] = sta.g[k] + flu.psnowlayer[k]


class Calc_ETG_V1(modeltools.Method):
    """Calculate thermal state for each snow layer.

        Basic equations:


    Examples:

        >>> from hydpy.models.snow import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> simulationstep('1d')
        >>> nsnowlayers(5)
        >>> cn1(0.962)
        >>> fluxes.tlayer =  -0.22318, -0.67402, -1.17348, -1.77018, -2.63208
        >>> states.etg = 1., -1., 0., 0., 0.
        >>> model.calc_etg_v1()
        >>> states.etg
        etg(0.0, -1.025613, -0.044592, -0.067267, -0.100019)
   """

    CONTROLPARAMETERS = (
        snow_control.NSnowLayers,
        snow_control.CN1,
    )

    REQUIREDSEQUENCES = (
        snow_fluxes.TLayer,
    )
    UPDATEDSEQUENCES = (
        snow_states.ETG,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess

        for k in range(con.nsnowlayers):
            sta.etg[k] = min(0, con.cn1 * sta.etg[k] + (1.0 - con.cn1) * flu.tlayer[k])


class Calc_PotMelt_V1(modeltools.Method):
    """Calculate potential melt for each snow layer.

        Basic equations:


    Examples:

        >>> from hydpy.models.snow import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> simulationstep('1d')
        >>> nsnowlayers(5)
        >>> cn2(2.249)
        >>> fluxes.tlayer = -1.0, 0.0, 0.5, 1.0, 1.5
        >>> states.g = 0.0, 1.0, 1.0, 10.0, 10.0
        >>> states.etg = 0.0, 1.0, 0.0, 0.0, 0.0
        >>> model.calc_potmelt_v1()
        >>> fluxes.potmelt
        potmelt(0.0, 0.0, 1.0, 2.249, 3.3735)
    """

    CONTROLPARAMETERS = (
        snow_control.NSnowLayers,
        snow_control.CN2,
    )

    REQUIREDSEQUENCES = (
        snow_fluxes.TLayer,
        snow_states.ETG,
        snow_states.G,
    )
    RESULTSEQUENCES = (
        snow_fluxes.PotMelt,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess

        for k in range(con.nsnowlayers):
            if sta.etg[k] == 0 and flu.tlayer[k] > 0:
                flu.potmelt[k] = min(sta.g[k], con.cn2 * flu.tlayer[k])
            else:
                flu.potmelt[k] = 0


class Calc_GRatio_V1(modeltools.Method):
    """Calculate snow covered area for each snow layer.

        Basic equations:


    Examples:

        >>> from hydpy.models.snow import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> simulationstep('1d')
        >>> nsnowlayers(5)
        >>> meanansolidprecip(80., 80., 80., 80., 80.)
        >>> states.g = 60., 70., 72., 80., 100.
        >>> model.calc_gratio_v1()
        >>> states.gratio
        gratio(0.833333, 0.972222, 1.0, 1.0, 1.0)
    """

    CONTROLPARAMETERS = (
        snow_control.NSnowLayers,
        snow_control.MeanAnSolidPrecip,
    )

    REQUIREDSEQUENCES = (
        snow_states.G,
    )
    UPDATEDSEQUENCES = (
        snow_states.GRatio,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        sta = model.sequences.states.fastaccess

        for k in range(con.nsnowlayers):
            d_gthreshold = 0.9 * con.meanansolidprecip[k]
            # todo: eigentlich derived gthresh mit cn4 = 0.9
            sta.gratio[k] = min(sta.g[k] / d_gthreshold, 1.0)


class Calc_GRatio_GLocalMax_V1(modeltools.Method):
    """Calculate snow covered area for each snow layer.

        Basic equations:


    Examples:

        >>> from hydpy.models.snow import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> simulationstep('1d')
        >>> nsnowlayers(5)
        >>> meanansolidprecip(80., 80., 80., 80., 80.)
        >>> states.g = 60., 70., 72., 80., 100.
        >>> model.calc_gratio_v1()
        >>> states.gratio
        gratio(0.833333, 0.972222, 1.0, 1.0, 1.0)
    """

    CONTROLPARAMETERS = (
        snow_control.NSnowLayers,
        snow_derived.GThresh,
    )

    REQUIREDSEQUENCES = (
        snow_states.G,
        snow_fluxes.PotMelt,
    )
    UPDATEDSEQUENCES = (
        snow_states.GRatio,
        snow_logs.GLocalMax,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.control.fastaccess
        sta = model.sequences.states.fastaccess
        log = model.sequences.logs.fastaccess
        flu = model.sequences.fluxes.fastaccess

        for k in range(con.nsnowlayers):
            if log.glocalmax[k] == 0.0:
                log.glocalmax[k] = der.gthresh[k]
            if flu.potmelt[k] > 0:
                # sta.glocalmax letzte Schneemenge, bei gratio=1
                # Setze neues glocalmax auf aktuelle Schneehöhe, falls alles Schnee
                if sta.gratio[k] == 1.0:
                    log.glocalmax[k] = min(sta.g[k], log.glocalmax[k])
                sta.gratio[k] = min(sta.g[k] / log.glocalmax[k], 1.0)


class Calc_Melt_V1(modeltools.Method):
    """Calculate snow accumulation for each snow layer.

        Basic equations:


    Examples:

        >>> from hydpy.models.snow import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> simulationstep('1d')
        >>> nsnowlayers(5)
        >>> fluxes.potmelt = (2.0, 2.0, 2.0, 2.0, 2.0)
        >>> states.gratio = 0.0, 0.25, 0.5, 0.75, 1.0
        >>> model.calc_melt_v1()
        >>> fluxes.melt
        melt(0.2, 0.65, 1.1, 1.55, 2.0)
    """

    CONTROLPARAMETERS = (
        snow_control.NSnowLayers,
    )

    REQUIREDSEQUENCES = (
        snow_fluxes.TLayer,
        snow_fluxes.PotMelt,
        snow_states.GRatio,
    )
    RESULTSEQUENCES = (
        snow_fluxes.Melt,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess

        d_minmelt = 0.1

        # todo: kann dazu führen, dass im Sommer (ganz wenig) Schnee liegt

        # umso mehr Schnee liegt, umso schneller schmilzt der Schnee (bis threshold)
        for k in range(con.nsnowlayers):
            flu.melt[k] = (
                (1.0 - d_minmelt) * sta.gratio[k] + d_minmelt
            ) * flu.potmelt[k]


class Update_G_V1(modeltools.Method):
    """Update snow pack according to snow melt

        Basic equations:


    Examples:

        >>> from hydpy.models.snow import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> simulationstep('1d')
        >>> nsnowlayers(5)
        >>> fluxes.melt = (0.0, 0.2, 0.2, 0.2, 0.2)
        >>> states.g = 0.0, 0.25, 0.5, 0.75, 1.0
        >>> model.update_g_v1()
        >>> states.g
        g(0.0, 0.05, 0.3, 0.55, 0.8)
    """

    CONTROLPARAMETERS = (
        snow_control.NSnowLayers,
    )

    DERIVEDPARAMETERS = (
        snow_derived.GThresh,
    )

    REQUIREDSEQUENCES = (
        snow_fluxes.Melt,
    )
    UPDATEDSEQUENCES = (
        snow_states.G,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess

        for k in range(con.nsnowlayers):
            sta.g[k] = sta.g[k] - flu.melt[k]


class Update_GRatio_GLocalMax_V1(modeltools.Method):
    """Update GRatio

        Basic equations:


    Examples:

        >>> from hydpy.models.snow import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> simulationstep('1d')
        >>> nsnowlayers(5)
        >>> cn3(1.0)
        >>> cn4(2.0)
        >>> derived.gthresh.update()
        >>> fluxes.psnowlayer = 0.0, 1.0, 2.0, 3.0, 4.0
        >>> fluxes.melt = 0.0, 0.0, 2.0, 2.0, 2.0
        >>> states.g = 1.0, 1.0, 1.0, 1.0, 1.0

        >>> states.gratio = 0.
        >>> logs.glocalmax = 0.
        >>> model.update_gratio_glocalmax_v1()

        >>> derived.gthresh
        >>> states.gratio
        gratio(0.0, 1.0, 0.0, 1.0, 1.0)
        >>> logs.glocalmax


    """

    CONTROLPARAMETERS = (
        snow_control.NSnowLayers,
        snow_control.CN3,
    )

    DERIVEDPARAMETERS = (
        snow_derived.GThresh,
    )

    REQUIREDSEQUENCES = (
        snow_fluxes.Melt,
        snow_fluxes.PSnowLayer,
    )
    UPDATEDSEQUENCES = (
        snow_states.GRatio,
        snow_logs.GLocalMax,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        log = model.sequences.logs.fastaccess

        for k in range(con.nsnowlayers):
            d_dg = flu.psnowlayer[k] - flu.melt[k]
            if d_dg > 0:
                # Aufbau der Schneedecke
                # Korrektur gratio durch Aufbau der Schneedecke
                sta.gratio[k] = min(
                    sta.gratio[k] + d_dg / con.cn3, 1.0
                )
                # Wenn alles Schnee, dann Abnahme mit gthresh
                if sta.gratio[k] == 1.0:
                    log.glocalmax[k] = der.gthresh[k]
            elif d_dg < 0:
                # wenn kein Aufbau der Schneedecke und mehr Schmelze als Aufbau
                sta.gratio[k] = min(sta.g[k] / log.glocalmax[k], 1.0)


class Model(modeltools.AdHocModel):
    """The snow base model."""

    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        Calc_PLayer_V1,
        Calc_TLayer_V1,
        Calc_TLayer_V2,
        Calc_FracSolidPrec_V1,
        Calc_FracSolidPrec_V2,
        Calc_G_V1,
        Calc_ETG_V1,
        Calc_PotMelt_V1,
        Calc_GRatio_V1,
        Calc_GRatio_GLocalMax_V1,
        Calc_Melt_V1,
        Update_G_V1,
        Update_GRatio_GLocalMax_V1,
    )
    ADD_METHODS = ()
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()
