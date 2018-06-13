"""Module for eta-omega maps"""
from __future__ import print_function

import numpy as np

from hexrd import matrixutil as mutil
from hexrd.valunits import valWUnit
from hexrd.xrd.transforms_CAPI import mapAngle

class GenerateEtaOmeMaps(object):
    """
    eta-ome map class derived from new image_series and YAML config

    ...for now...

    must provide:

    self.dataStore
    self.planeData
    self.iHKLList
    self.etaEdges # IN RADIANS
    self.omeEdges # IN RADIANS
    self.etas     # IN RADIANS
    self.omegas   # IN RADIANS

    """
    def __init__(self, image_series_dict, instrument, plane_data,
                 active_hkls=None, eta_step=0.25, threshold=None,
                 ome_period=(0, 360)):
        """
        image_series must be OmegaImageSeries class
        instrument_params must be a dict (loaded from yaml spec)
        active_hkls must be a list (required for now)
        """

        self._planeData = plane_data

        # ???: change name of iHKLList?
        # ???: can we change the behavior of iHKLList?
        if active_hkls is None:
            n_rings = len(plane_data.getTTh())
            self._iHKLList = range(n_rings)
        else:
            self._iHKLList = active_hkls
            n_rings = len(active_hkls)

        # ???: need to pass a threshold?
        eta_mapping, etas = instrument.extract_polar_maps(
            plane_data, image_series_dict,
            active_hkls=active_hkls, threshold=threshold,
            tth_tol=None, eta_tol=eta_step)

        # grab a det key
        # WARNING: this process assumes that the imageseries for all panels
        # have the same length and omegas
        det_key = eta_mapping.keys()[0]
        data_store = []
        for i_ring in range(n_rings):
            full_map = np.zeros_like(eta_mapping[det_key][i_ring])
            nan_mask_full = np.zeros(
                (len(eta_mapping), full_map.shape[0], full_map.shape[1])
            )
            i_p = 0
            for det_key, eta_map in eta_mapping.iteritems():
                nan_mask = ~np.isnan(eta_map[i_ring])
                nan_mask_full[i_p] = nan_mask
                full_map[nan_mask] += eta_map[i_ring][nan_mask]
                i_p += 1
            re_nan_these = np.sum(nan_mask_full, axis=0) == 0
            full_map[re_nan_these] = np.nan
            data_store.append(full_map)
        self._dataStore = data_store

        # handle omegas
        omegas_array = image_series_dict[det_key].metadata['omega']
        self._omegas = mapAngle(
            np.radians(np.average(omegas_array, axis=1)),
            np.radians(ome_period)
        )
        self._omeEdges = mapAngle(
            np.radians(np.r_[omegas_array[:, 0], omegas_array[-1, 1]]),
            np.radians(ome_period)
        )

        # handle etas
        # WARNING: unlinke the omegas in imageseries metadata,
        # these are in RADIANS and represent bin centers
        self._etas = etas
        self._etaEdges = np.r_[
            etas - 0.5*np.radians(eta_step),
            etas[-1] + 0.5*np.radians(eta_step)]

    @property
    def dataStore(self):
        return self._dataStore

    @property
    def planeData(self):
        return self._planeData

    @property
    def iHKLList(self):
        return np.atleast_1d(self._iHKLList).flatten()

    @property
    def etaEdges(self):
        return self._etaEdges

    @property
    def omeEdges(self):
        return self._omeEdges

    @property
    def etas(self):
        return self._etas

    @property
    def omegas(self):
        return self._omegas

    def save(self, filename):
        """
        self.dataStore
        self.planeData
        self.iHKLList
        self.etaEdges
        self.omeEdges
        self.etas
        self.omegas
        """
        args = np.array(self.planeData.getParams())[:4]
        args[2] = valWUnit('wavelength', 'length', args[2], 'angstrom')
        hkls = self.planeData.hkls
        save_dict = {'dataStore': self.dataStore,
                     'etas': self.etas,
                     'etaEdges': self.etaEdges,
                     'iHKLList': self.iHKLList,
                     'omegas': self.omegas,
                     'omeEdges': self.omeEdges,
                     'planeData_args': args,
                     'planeData_hkls': hkls}
        np.savez_compressed(filename, **save_dict)
        return
    pass  # end of class: GenerateEtaOmeMaps
