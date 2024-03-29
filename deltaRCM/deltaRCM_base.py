from math import floor, sqrt
import numpy as np
from random import shuffle
from matplotlib import pyplot as plt
from scipy import ndimage
import sys, os, re, string
import pickle

from deltaRCM_tools import save_figure, random_pick, random_pick_list

class Tools(object):

    _input_vars = {
        'model_output__site_prefix': {'name':'site_prefix', 'type': 'string', 'default': ''},
        'model_output__case_prefix': {'name':'case_prefix', 'type': 'string', 'default': ''},
        'model_output__out_dir': {'name':'out_dir', 'type': 'string', 'default': 'deltaRCM_Output/'},
        'model__total_timesteps': {'name':'n_steps', 'type': 'long', 'default': 200},
        'model_grid__length': {'name':'Length', 'type': 'float', 'default': 200.},
        'model_grid__width': {'name':'Width', 'type': 'float', 'default': 500.},
        'model_grid__cell_size': {'name':'dx', 'type': 'float', 'default': 10.},
        'land_surface__width': {'name':'L0_meters', 'type': 'float', 'default': 30.}, 
        'land_surface__slope': {'name':'S0', 'type': 'float', 'default': 0.00015},
        'model__max_iteration': {'name':'itermax', 'type': 'long', 'default': 3},
        'water__number_parcels': {'name':'Np_water', 'type': 'long', 'default': 200},
        'channel__flow_velocity': {'name':'u0', 'type': 'float', 'default': 1.},
        'channel__width': {'name':'N0_meters', 'type': 'float', 'default': 50.},
        'channel__flow_depth': {'name':'h0', 'type': 'float', 'default': 5.},
        'sea_water_surface__elevation': {'name':'H_SL', 'type': 'float', 'default': 0.},
        'sea_water_surface__rate_change_elevation': {'name':'SLR', 'type': 'float', 'default': 0.},
        'sediment__number_parcels': {'name':'Np_sed', 'type': 'long', 'default': 500},
        'sediment__bedload_fraction': {'name':'f_bedload', 'type': 'float', 'default': 0.25}, 
        'sediment__influx_concentration': {'name':'C0_percent', 'type': 'float', 'default': 0.1},                   
        'model_output__opt_eta_figs': {'name':'save_eta_figs', 'type': 'choice', 'default': False},
        'model_output__opt_stage_figs': {'name':'save_stage_figs', 'type': 'choice', 'default': False},
        'model_output__opt_depth_figs': {'name':'save_depth_figs', 'type': 'choice', 'default': False},
        'model_output__opt_eta_grids': {'name':'save_eta_grids', 'type': 'choice', 'default': False},
        'model_output__opt_stage_grids': {'name':'save_stage_grids', 'type': 'choice', 'default': False},
        'model_output__opt_depth_grids': {'name':'save_depth_grids', 'type': 'choice', 'default': False},
        'model_output__opt_time_interval': {'name':'save_dt', 'type': 'long', 'default': 10},
        'coeff__surface_smoothing': {'name': 'Csmooth', 'type': 'float', 'default': 0.9},
        'coeff__under_relaxation__water_surface': {'name': 'omega_sfc', 'type': 'float', 'default': 0.1},
        'coeff__under_relaxation__water_flow': {'name': 'omega_flow', 'type': 'float', 'default': 0.9},
        'coeff__iterations_smoothing_algorithm': {'name': 'Nsmooth', 'type': 'long', 'default': 5},
        'coeff__depth_dependence__water': {'name': 'theta_water', 'type': 'float', 'default': 1.0},
        'coeff__depth_dependence__sand': {'name': 'coeff_theta_sand', 'type': 'float', 'default': 2.0},
        'coeff__depth_dependence__mud': {'name': 'coeff_theta_mud', 'type': 'float', 'default': 1.0},
        'coeff__non_linear_exp_sed_flux_flow_velocity': {'name': 'beta', 'type': 'long', 'default': 3},
        'coeff__sedimentation_lag': {'name': 'sed_lag', 'type': 'float', 'default': 1.0},
        'coeff__velocity_deposition_mud': {'name': 'coeff_U_dep_mud', 'type': 'float', 'default': 0.3},
        'coeff__velocity_erosion_mud': {'name': 'coeff_U_ero_mud', 'type': 'float', 'default': 1.5},
        'coeff__velocity_erosion_sand': {'name': 'coeff_U_ero_sand', 'type': 'float', 'default': 1.05},
        'coeff__topographic_diffusion': {'name': 'alpha', 'type': 'float', 'default': 0.1}
        }


    def flatten_indices(self, ind):
        '''Flatten indices'''

        return ind[0]*self.W + ind[1]


    def output_data(self, timestep):

        if int(timestep+1) % self.save_dt == 0:
    
            if self.save_eta_figs:
                    
                plt.pcolor(self.eta)
                plt.colorbar()
                save_figure(self.prefix + "eta" + str(timestep+1))
            
            if self.save_stage_figs:
                    
                plt.pcolor(self.stage)
                plt.colorbar()
                save_figure(self.prefix + "stage" + str(timestep+1))
                        
            if self.save_depth_figs:
                    
                plt.pcolor(self.depth)
                plt.colorbar()
                save_figure(self.prefix + "depth" + str(timestep+1))
                
                


    #############################################
    ############### weight arrays ###############
    #############################################

    def build_weight_array(self, array, fix_edges = False, normalize = False):
        '''
        Create np.array((8,L,W)) of quantity a in each of the neighbors to a cell
        '''

        self.array = array
        a_shape = array.shape

        self.fix_edges = fix_edges
        self.normalize = normalize

        wgt_array = np.zeros((8,a_shape[0],a_shape[1]))
        nums = range(8)

        wgt_array[nums[0],:,:-1] = self.array[:,1:] # E
        wgt_array[nums[1],1:,:-1] = self.array[:-1,1:] # NE
        wgt_array[nums[2],1:,:] = self.array[:-1,:] # N
        wgt_array[nums[3],1:,1:] = self.array[:-1,:-1] # NW
        wgt_array[nums[4],:,1:] = self.array[:,:-1] # W
        wgt_array[nums[5],:-1,1:] = self.array[1:,:-1] # SW
        wgt_array[nums[6],:-1,:] = self.array[1:,:] # S
        wgt_array[nums[7],:-1,:-1] = self.array[1:,1:] # SE

        if self.fix_edges:
            wgt_array[nums[0],:,-1] = wgt_array[nums[0],:,-2]
            wgt_array[nums[1],:,-1] = wgt_array[nums[1],:,-2]
            wgt_array[nums[7],:,-1] = wgt_array[nums[7],:,-2]
            wgt_array[nums[1],0,:] = wgt_array[nums[1],1,:]
            wgt_array[nums[2],0,:] = wgt_array[nums[2],1,:]
            wgt_array[nums[3],0,:] = wgt_array[nums[3],1,:]
            wgt_array[nums[3],:,0] = wgt_array[nums[3],:,1]
            wgt_array[nums[4],:,0] = wgt_array[nums[4],:,1]
            wgt_array[nums[5],:,0] = wgt_array[nums[5],:,1]
            wgt_array[nums[5],-1,:] = wgt_array[nums[5],-2,:]
            wgt_array[nums[6],-1,:] = wgt_array[nums[6],-2,:]
            wgt_array[nums[7],-1,:] = wgt_array[nums[7],-2,:]

        if self.normalize:
            a_sum = np.sum(wgt_array, axis=0)
            wgt_array[:,a_sum!=0] = wgt_array[:,a_sum!=0] / a_sum[a_sum!=0]

        return wgt_array



    def get_wet_mask_nh(self):
        '''
        Get np.array((8,L,W)) for each neighbor around a cell
        with 1 if te neighbor is wet and 0 if dry
        '''

        wet_mask = (self.depth > self.dry_depth) * 1
        wet_mask_nh = self.build_weight_array(wet_mask, fix_edges = True)

        return wet_mask_nh



    def get_wgt_sfc(self, wet_mask_nh):
        '''
        Get np.array((8,L,W)) (H - H_neighbor)/dist
        for each neighbor around a cell

        Takes an narray of the same size with 1 if wet and 0 if not
        '''

        wgt_sfc = self.build_weight_array(self.stage, fix_edges = True)

        wgt_sfc = (self.stage - wgt_sfc) / np.array(self.dxn_dist)[:, np.newaxis, np.newaxis]

        wgt_sfc = wgt_sfc * wet_mask_nh
        wgt_sfc[wgt_sfc<0] = 0

        wgt_sfc_sum = np.sum(wgt_sfc,axis=0)
        wgt_sfc[:,wgt_sfc_sum>0] = wgt_sfc[:,wgt_sfc_sum>0] / wgt_sfc_sum[wgt_sfc_sum>0]

        return wgt_sfc



    def get_wgt_int(self, wet_mask_nh):
        '''
        Get np.array((8,L,W)) (qx*dxn_ivec + qy*dxn_jvec)/dist
        for each neighbor around a cell

        Takes an narray of the same size with 1 if wet and 0 if not
        '''

        wgt_int = (self.qx * np.array(self.dxn_ivec)[:,np.newaxis,np.newaxis] + \
            self.qy * np.array(self.dxn_jvec)[:,np.newaxis,np.newaxis]) / \
            np.array(self.dxn_dist)[:,np.newaxis,np.newaxis]

        wgt_int[1:4,0,:] = 0

        wgt_int = wgt_int * wet_mask_nh
        wgt_int[wgt_int<0] = 0
        wgt_int_sum = np.sum(wgt_int, axis=0)

        wgt_int[:,wgt_int_sum>0] = wgt_int[:,wgt_int_sum>0]/wgt_int_sum[wgt_int_sum>0]

        return wgt_int



    def get_wgt(self):
        '''
        Get np.array((8,L,W)) of the probabilities of flow
        between a cell and each of its neighbors

        If the probabilities are zero in all directions, they will
        be split equally among all wet neighbors
        '''

        wet_mask_nh = self.get_wet_mask_nh()
        wgt_sfc = self.get_wgt_sfc(wet_mask_nh)
        wgt_int = self.get_wgt_int(wet_mask_nh)


        weight = self.gamma * wgt_sfc + (1-self.gamma) * wgt_int

        wgt = self.build_weight_array(self.depth, fix_edges = True)
        wgt = wgt**self.theta_water * weight

        wet_mask = 1*(self.depth > self.dry_depth)
        wgt = wgt * wet_mask
        wgt[wgt<0] = 0
        wgt_sum = np.sum(wgt,axis=0)
        wgt[:,wgt_sum>0] = wgt[:,wgt_sum>0] / wgt_sum[wgt_sum>0]

        # give wet cells with zero wgt to all wet neighbors equal probs for each of them
        # wet cells with zero probabilities to all neighbors
        wet_mask = 1*(self.depth > self.dry_depth)

        wet_cells = np.where((wgt_sum + (wet_mask-1)) == 0)

        wet = [(wet_cells[0][i],wet_cells[1][i]) for i in range(len(wet_cells[0]))]

        # new weights to those cells - partitioned equally among the wet neighbors
        new_vals = [wet_mask_nh[:,i[0],i[1]]/sum(wet_mask_nh[:,i[0],i[1]]) for i in wet]

        for i in range(len(new_vals)):
            wgt[:,wet[i][0],wet[i][1]] = new_vals[i]

        wgt[1:4,0,:] = 0

        return wgt



    def get_sed_weight(self):
        '''
        Get np.array((8,L,W)) of probability field of routing to neighbors
        for sediment parcels
        '''

        wet_mask_nh = self.get_wet_mask_nh()

        weight = self.get_wgt_int(wet_mask_nh) * \
            self.depth**self.theta_sand * wet_mask_nh

        weight[weight<0] = 0.
        weight_sum = np.sum(weight,axis=0)
        weight[:,weight_sum>0] = weight[:,weight_sum>0]/weight_sum[weight_sum>0]

        weight_f = np.zeros((self.L*self.W,8))

        for i in range(8):
            weight_f[:,i] = weight[i,:,:].flatten()

        return weight_f



    #############################################
    ################# smoothing #################
    #############################################

    def smoothing_filter(self, stageTemp):
        '''
        Smooth water surface

        If any of the cells in a 9-cell window are wet, apply this filter

        stageTemp : water surface
        stageT : smoothed water surface
        '''

        stageT = stageTemp.copy()
        wet_mask = self.depth > self.dry_depth

        for t in range(self.Nsmooth):

            local_mean = ndimage.uniform_filter(stageT)

            stageT[wet_mask] = self.Csmooth * stageT[wet_mask] + \
                (1-self.Csmooth) * local_mean[wet_mask]

        returnval = (1-self.omega_sfc) * self.stage + self.omega_sfc * stageT

        return returnval



    def flooding_correction(self):
        '''
        Flood dry cells along the shore if necessary

        Check the neighbors of all dry cells. If any dry cells have wet neighbors
        Check that their stage is not higher than the bed elevation of the center cell
        If it is, flood the dry cell
        '''

        wet_mask = self.depth > self.dry_depth
        wet_mask_nh = self.get_wet_mask_nh()
        wet_mask_nh_sum = np.sum(wet_mask_nh, axis=0)

        # makes wet cells look like they have only dry neighbors
        wet_mask_nh_sum[wet_mask] = 0

        # indices of dry cells with wet neighbors
        shore_ind = np.where(wet_mask_nh_sum > 0)

        stage_nhs = self.build_weight_array(self.stage)
        eta_shore = self.eta[shore_ind]

        for i in range(len(shore_ind[0])):

            # pretends dry neighbor cells have stage zero so they cannot be > eta_shore[i]
            stage_nh = wet_mask_nh[:,shore_ind[0][i],shore_ind[1][i]] * \
                stage_nhs[:,shore_ind[0][i],shore_ind[1][i]]

            if (stage_nh > eta_shore[i]).any():
                self.stage[shore_ind[0][i],shore_ind[1][i]] = max(stage_nh)



    def topo_diffusion(self):
        '''
        Diffuse topography after routing all coarse sediment parcels
        '''

        wgt_cell_type = self.build_weight_array(self.cell_type > -2)
        wgt_qs = self.build_weight_array(self.qs) + self.qs
        wet_mask_nh = self.get_wet_mask_nh()

        multiplier = self.dt/self.N_crossdiff * self.alpha * 0.5 / self.dx**2

        for n in range(self.N_crossdiff):

            wgt_eta = self.build_weight_array(self.eta) - self.eta

            crossflux_nb = multiplier * wgt_qs * wgt_eta

            crossflux_nb = crossflux_nb * wet_mask_nh

            crossflux = np.sum(crossflux_nb, axis=0)
            self.eta = self.eta + crossflux



    #############################################
    ################# updaters ##################
    #############################################

    def update_flow_field(self, timestep, iteration):
        '''
        Update water discharge after one water iteration
        '''

        dloc = (self.qxn**2 + self.qyn**2)**(0.5)
        qwn_div = np.ones_like(self.qwn)
        qwn_div[dloc>0] = self.qwn[dloc>0] / dloc[dloc>0]
        self.qxn *= qwn_div
        self.qyn *= qwn_div

        if timestep > 0:

            omega = self.omega_flow_iter
            if iteration == 0: omega = self.omega_flow

            self.qx = self.qxn*omega + self.qx*(1-omega)
            self.qy = self.qyn*omega + self.qy*(1-omega)

        else:

            self.qx = self.qxn.copy(); self.qy = self.qyn.copy()

        self.qw = (self.qx**2 + self.qy**2)**(0.5)
        self.qx[0,self.inlet] = self.qw0
        self.qy[0,self.inlet] = 0
        self.qw[0,self.inlet] = self.qw0



    def update_velocity_field(self):
        '''
        Update the flow velocity field after one water iteration
        '''

        mask = (self.depth > self.dry_depth) * (self.qw > 0)
        self.uw[mask] = np.minimum(self.u_max, self.qw[mask] / self.depth[mask])
        self.uw[~mask] = 0
        self.ux[mask]= self.uw[mask] * self.qx[mask] / self.qw[mask]
        self.ux[~mask] = 0
        self.uy[mask]= self.uw[mask] * self.qy[mask] / self.qw[mask]
        self.uy[~mask] = 0



    #############################################
    ################# water flow ################
    #############################################

    def init_water_iteration(self):

        wgt = self.get_wgt()

        for i in range(8):
            self.wgt_flat[:,i] = wgt[i,:,:].flatten()

        self.qxn[:] = 0; self.qyn[:] = 0; self.qwn[:] = 0

        self.indices = np.zeros((self.Np_water, self.itmax/2), dtype = np.int)
        self.path_number = np.array(range(self.Np_water))
        self.save_paths = []



    def run_water_iteration(self):
        '''
        Route all parcels of water in one iteration
        '''

        these_indices = map(lambda x: self.random_pick_list(self.inlet), range(self.Np_water))
        these_indices = map(self.flatten_indices, these_indices)

        self.indices[:,0] = these_indices
        self.qxn.flat[these_indices] += 1

        water_continue = True
        it = 0

        while water_continue:

            ngh = map(self.random_pick, self.wgt_flat[these_indices])
            new_indices = these_indices + self.walk_flat[ngh]
            new_ind_type = self.cell_type.flat[new_indices]

            # save the path numbers of the ones that reached the edge
            if self.path_number[new_ind_type == -1].any():
                self.save_paths.append( list(self.path_number[new_ind_type == -1]) )

            walk_vals = self.walk[ngh]
            self.qxn.flat[these_indices] += walk_vals[:,0]
            self.qyn.flat[these_indices] += walk_vals[:,1]

            walk_vals = self.walk[list( np.array(ngh)[new_ind_type >= -1] )]
            n_these_indices = new_indices[new_ind_type >= -1]
            n_path_number = self.path_number[new_ind_type >= -1]
            for i in range(len(n_these_indices)):
                self.qxn.flat[n_these_indices[i]] += walk_vals[i,0]
                self.qyn.flat[n_these_indices[i]] += walk_vals[i,1]

            it += 1
            self.indices[n_path_number,it] = n_these_indices

            these_indices = new_indices[new_ind_type >= 0]
            self.path_number = self.path_number[new_ind_type >= 0]

            # check for looping
            if len(self.path_number)>0:
                keeper = np.ones((len(these_indices),), dtype=np.int)
                for i in range(len(these_indices)):

                    if np.in1d(self.indices[self.path_number[i],:it], these_indices[i]).any():
                        keeper[i] = 0

                    if these_indices[i]<0:
                        keeper[i] = 0

                if np.min(keeper)==0:

                    these_indices = these_indices[keeper == 1]
                    self.path_number = self.path_number[keeper == 1]

            if it == self.itmax-1 or len(these_indices)==0:
                water_continue = False

        # update qwn by counting the indices
        all_indices = self.indices.flatten()
        all_indices.sort()
        loc = np.where(all_indices>0)[0][0]
        ind_index_all = all_indices[loc:]

        ind_count = np.bincount(ind_index_all)
        ind_index = range(max(ind_index_all)+1)

        qwn_sum = ind_count[ind_index] * self.Qp_water/self.dx

        self.qwn.flat[ind_index] += qwn_sum



    def finalize_water_iteration(self, timestep, iteration):
        '''
        Finish updating flow fields
        Clean up at end of water iteration
        '''

        self.flooding_correction()
        self.stage = np.maximum(self.stage, self.H_SL)
        self.depth = np.maximum(self.stage - self.eta, 0)

        self.update_flow_field(timestep, iteration)
        self.update_velocity_field()



    def get_profiles(self):
        '''
        Calculate the water surface profiles after routing flow parcels
        Update water surface array
        '''

        paths_for_profile = [i for j in self.save_paths for i in j]

        assert len(paths_for_profile) == len(set(paths_for_profile)), "save_paths has repeats!"

        # get all the unique indices in good paths
        unique_cells = list(set([j for i in paths_for_profile for j in list(set(self.indices[i]))]))
        try:
            unique_cells.remove(0)
        except:
            pass

        unique_cells.sort()

        # extract the values needed for the paths -- no need to do this for the entire space
        uw_unique = self.uw.flat[unique_cells]
        depth_unique = self.depth.flat[unique_cells]
        ux_unique = self.ux.flat[unique_cells]
        uy_unique = self.uy.flat[unique_cells]

        profile_mask = np.add(uw_unique > 0.5*self.u0, depth_unique < 0.1*self.h0)

        all_unique = zip(profile_mask,uw_unique,ux_unique,uy_unique)

        sfc_array = np.zeros((len(unique_cells),2))

        # make dictionaries to use as lookup tables
        lookup = {}
        self.sfc_change = {}

        for i in range(len(unique_cells)):
            lookup[unique_cells[i]] = all_unique[i]
            self.sfc_change[unique_cells[i]] = sfc_array[i]

        # process each profile
        for i in paths_for_profile:

            path = self.indices[i]
            path = path[np.where(path>0)]

            prf = [lookup[i][0] for i in path]

            # find the last True
            try:
                last_True = (len(prf) - 1) - prf[::-1].index(True)
                sub_path = path[:last_True]

                sub_path_unravel = np.unravel_index(sub_path, self.eta.shape)

                path_diff = np.diff(sub_path_unravel)
                ux_ = [lookup[i][2] for i in sub_path[:-1]]
                uy_ = [lookup[i][3] for i in sub_path[:-1]]
                uw_ = [lookup[i][1] for i in sub_path[:-1]]

                dH = self.S0 * (ux_ * path_diff[0] + uy_ * path_diff[1]) * self.dx
                dH = [dH[i] / uw_[i] if uw_[i]>0 else 0 for i in range(len(dH))]
                dH.append(0)

                newH = np.zeros(len(sub_path))
                for i in range(-2,-len(sub_path)-1,-1):
                    newH[i] = newH[i+1] + dH[i]

                for i in range(len(sub_path)):
                    self.sfc_change[sub_path[i]] += [newH[i],1]
            except:
                pass

        stageTemp = self.eta + self.depth

        for k, v in self.sfc_change.iteritems():
            if np.max(v) > 0:
                stageTemp.flat[k] = v[0]/v[1]

        self.stage = self.smoothing_filter(stageTemp)



    #############################################
    ################# sed flow ##################
    #############################################

    def init_sed_timestep(self):
        '''
        Set up arrays to start sed routing timestep
        '''

        self.qs[:] = 0
        self.Vp_dep_sand[:] = 0
        self.Vp_dep_mud[:] = 0



    def one_fine_timestep(self):
        '''
        Route all parcels of fine sediment
        '''

        self.num_fine = int(self.Np_sed - self.num_coarse)

        if self.num_fine>0:

            these_indices = map(lambda x: self.random_pick_list(self.inlet),range(self.num_fine))
            these_indices = map(self.flatten_indices,these_indices)

            self.indices = np.zeros((self.num_fine,self.itmax), dtype=np.int)
            self.indices[:,0] = these_indices

            path_number = np.array(range(self.num_fine))
            self.Vp_res = np.zeros((self.Np_sed,)) + self.Vp_sed
            self.qs.flat[these_indices] += self.Vp_res[path_number]/2/self.dt/self.dx

            sed_continue = True
            it = 0

            while sed_continue:

                weight = self.get_sed_weight()

                ngh = map(self.random_pick, weight[these_indices])
                new_indices = these_indices + self.walk_flat[ngh]
                new_ind_type = self.cell_type.flat[new_indices]

                self.qs.flat[these_indices] += self.Vp_res[path_number]/2/self.dt/self.dx
                self.qs.flat[new_indices] += self.Vp_res[path_number]/2/self.dt/self.dx


                these_indices = new_indices[new_ind_type >= 0]
                path_number = path_number[new_ind_type >= 0]

                if len(path_number)>0:
                    # check for looping
                    keeper = np.ones((len(these_indices),), dtype=np.int)
                    for i in range(len(these_indices)):
                        if np.in1d(self.indices[path_number[i],:], these_indices[i]).any():
                            keeper[i] = 0
                        if these_indices[i]<0:
                            keeper[i] = 0
                    if np.min(keeper)==0:
                        these_indices = these_indices[keeper == 1]
                        path_number = path_number[keeper == 1]

                # save to the master indices
                it += 1
                self.indices[path_number,it] = these_indices


                if (self.uw.flat[these_indices] < self.U_dep_mud).any():

                    update_ind = these_indices[self.uw.flat[these_indices] < self.U_dep_mud]
                    update_path = path_number[self.uw.flat[these_indices] < self.U_dep_mud]
                    Vp_res_ = self.Vp_res[update_path]

                    Vp_res_ = self.sed_lag * Vp_res_ * (self.U_dep_mud**self.beta - self.uw.flat[update_ind]**self.beta) / (self.U_dep_mud**self.beta)

                    self.Vp_dep = (self.stage.flat[update_ind] - self.eta.flat[update_ind])/4 * self.dx**2
                    self.Vp_dep = np.array([min((Vp_res_[i],self.Vp_dep[i])) for i in range(len(self.Vp_dep))])
                    self.Vp_dep_mud.flat[update_ind] += self.Vp_dep

                    self.Vp_res[update_path] -= self.Vp_dep

                    self.eta.flat[update_ind] += self.Vp_dep / self.dx**2
                    self.depth.flat[update_ind] = self.stage.flat[update_ind] - self.eta.flat[update_ind]
                    update_uw = [min(self.u_max, self.qw.flat[i]/self.depth.flat[i]) for i in update_ind]
                    self.uw.flat[update_ind] = update_uw

                    update_uwqw = [self.uw.flat[i]/self.qw.flat[i] if self.qw.flat[i]>0 else 0 for i in update_ind]
                    self.ux.flat[update_ind] = self.qx.flat[update_ind] * update_uwqw
                    self.uy.flat[update_ind] = self.qy.flat[update_ind] * update_uwqw


                if (self.uw.flat[these_indices] > self.U_ero_mud).any():

                    update_ind = these_indices[self.uw.flat[these_indices] > self.U_ero_mud]
                    update_path = path_number[self.uw.flat[these_indices] > self.U_ero_mud]

                    Vp_res_ = self.Vp_sed * (self.uw.flat[update_ind]**self.beta - self.U_ero_mud**self.beta) / (self.U_ero_mud**self.beta)
                    self.Vp_ero = (self.stage.flat[update_ind] - self.eta.flat[update_ind])/4 * self.dx**2
                    self.Vp_ero = np.array([min((Vp_res_[i],self.Vp_ero[i])) for i in range(len(self.Vp_ero))])

                    self.eta.flat[update_ind] -= self.Vp_ero / self.dx**2

                    self.depth.flat[update_ind] = self.stage.flat[update_ind] - self.eta.flat[update_ind]
                    update_uw = [min(self.u_max, self.qw.flat[i]/self.depth.flat[i]) for i in update_ind]
                    self.uw.flat[update_ind] = update_uw

                    update_uwqw = [self.uw.flat[i]/self.qw.flat[i] if self.qw.flat[i]>0 else 0 for i in update_ind]
                    self.ux.flat[update_ind] = self.qx.flat[update_ind] * update_uwqw
                    self.uy.flat[update_ind] = self.qy.flat[update_ind] * update_uwqw

                    self.Vp_res[update_path] += self.Vp_ero


                if it == self.itmax-1 or len(these_indices)==0:
                    sed_continue = False



    def one_coarse_timestep(self):
        '''
        Route all parcels of coarse sediment
        '''

        self.num_coarse = int(round(self.Np_sed*self.f_bedload))

        if self.num_coarse>0:

            these_indices = map(lambda x: self.random_pick_list(self.inlet),range(self.num_coarse))
            these_indices = map(self.flatten_indices,these_indices)

            self.indices = np.zeros((self.num_coarse,self.itmax), dtype=np.int)
            self.indices[:,0] = these_indices

            path_number = np.array(range(self.num_coarse))
            self.Vp_res = np.zeros((self.Np_sed,)) + self.Vp_sed
            self.qs.flat[these_indices] += self.Vp_res[path_number]/2/self.dt/self.dx

            sed_continue = True
            it = 0

            while sed_continue:

                weight = self.get_sed_weight()

                ngh = map(self.random_pick, weight[these_indices])
                new_indices = these_indices + self.walk_flat[ngh]
                new_ind_type = self.cell_type.flat[new_indices]

                self.qs.flat[these_indices] += self.Vp_res[path_number]/2/self.dt/self.dx
                self.qs.flat[new_indices] += self.Vp_res[path_number]/2/self.dt/self.dx

                these_indices = new_indices[new_ind_type >= 0]
                path_number = path_number[new_ind_type >= 0]

                if len(path_number)>0:
                    # check for looping
                    keeper = np.ones((len(these_indices),), dtype=np.int)
                    for i in range(len(these_indices)):
                        if np.in1d(self.indices[path_number[i],:], these_indices[i]).any():
                            keeper[i] = 0
                        if these_indices[i]<0:
                            keeper[i] = 0
                    if np.min(keeper)==0:
                        these_indices = these_indices[keeper == 1]
                        path_number = path_number[keeper == 1]

                it += 1
                self.indices[path_number,it] = these_indices

                qs_cap = self.qs0 * self.f_bedload/self.u0**self.beta * self.uw.flat[these_indices]**self.beta


                if (self.qs.flat[these_indices] > qs_cap).any():

                    update_ind = these_indices[self.qs.flat[these_indices] > qs_cap]
                    update_path = path_number[self.qs.flat[these_indices] > qs_cap]
                    Vp_res_ = self.Vp_res[update_path]

                    self.Vp_dep = (self.stage.flat[update_ind] - self.eta.flat[update_ind])/4 * self.dx**2
                    self.Vp_dep = np.array([min((Vp_res_[i],self.Vp_dep[i])) for i in range(len(update_ind))])
                    eta_change = self.Vp_dep / self.dx**2
                    self.Vp_res[update_path] -= self.Vp_dep
                    self.Vp_dep_sand.flat[update_ind] += self.Vp_dep

                    self.eta.flat[update_ind] += eta_change

                    update_uw = [min(self.u_max, self.qw.flat[i]/self.depth.flat[i]) for i in update_ind]
                    self.uw.flat[update_ind] = update_uw

                    update_uwqw = [self.uw.flat[i]/self.qw.flat[i] if self.qw.flat[i]>0 else 0 for i in update_ind]
                    self.ux.flat[update_ind] = self.qx.flat[update_ind] * update_uwqw
                    self.uy.flat[update_ind] = self.qy.flat[update_ind] * update_uwqw


                if ((self.qs.flat[these_indices] < qs_cap) * (self.uw.flat[these_indices] > self.U_ero_sand)).any():

                    update_ind = these_indices[(self.qs.flat[these_indices] < qs_cap) * (self.uw.flat[these_indices] > self.U_ero_sand)]
                    update_path = path_number[(self.qs.flat[these_indices] < qs_cap) * (self.uw.flat[these_indices] > self.U_ero_sand)]

                    Vp_res_ = self.Vp_sed * (self.uw.flat[update_ind]**self.beta - self.U_ero_sand**self.beta) / (self.U_ero_sand**self.beta)
                    Vp_ero_ = (self.stage.flat[update_ind] - self.eta.flat[update_ind])/4 * self.dx**2
                    self.Vp_ero = np.array([min((Vp_res_[i],Vp_ero_[i])) for i in range(len(update_ind))])

                    self.eta.flat[update_ind] -= self.Vp_ero / self.dx**2
                    self.depth.flat[update_ind] = self.stage.flat[update_ind] - self.eta.flat[update_ind]


                    update_uw = [min(self.u_max, self.qw.flat[i]/self.depth.flat[i]) for i in update_ind]
                    self.uw.flat[update_ind] = update_uw

                    update_uwqw = [self.uw.flat[i]/self.qw.flat[i] if self.qw.flat[i]>0 else 0 for i in update_ind]
                    self.ux.flat[update_ind] = self.qx.flat[update_ind] * update_uwqw
                    self.uy.flat[update_ind] = self.qy.flat[update_ind] * update_uwqw

                    self.Vp_res[update_path] += self.Vp_ero


                if it == self.itmax-1 or len(these_indices)==0:
                    sed_continue = False

        self.topo_diffusion()



    def finalize_sed_timestep(self):
        '''
        Clean up after sediment routing
        Update sea level if baselevel changes
        '''

        self.flooding_correction()
        self.stage = np.maximum(self.stage, self.H_SL)
        self.depth = np.maximum(self.stage-self.eta, 0)

        self.eta[0,self.inlet] = self.stage[0,self.inlet] - self.h0
        self.depth[0,self.inlet] = self.h0

        self.H_SL = self.H_SL + self.SLR * self.dt



    #############################################
    ############## initialization ###############
    #############################################

    def get_var_name(self, long_var_name): 
        return self._var_name_map[ long_var_name ]


    def import_file(self):

        if self.verbose: print 'Reading input file...'

        self.input_file_vars = dict()
        numvars = 0

        o = open(self.input_file, mode = 'r')

        for line in o:
            line = re.sub('\s$','',line)
            line = re.sub('\A[: :]*','',line)
            ln = re.split('\s*[\:\=]\s*', line)

            if len(ln)>1:

                ln[0] = string.lower(ln[0])

                if ln[0] in self._input_var_names:

                    numvars += 1

                    var_type = self._var_type_map[ln[0]]

                    ln[1] = re.sub('[: :]+$','',ln[1])

                    if var_type == 'string':
                        self.input_file_vars[str(ln[0])] = str(ln[1])
                    if var_type == 'float':
                        self.input_file_vars[str(ln[0])] = float(ln[1])
                    if var_type == 'long':
                        self.input_file_vars[str(ln[0])] = int(ln[1])
                    if var_type == 'choice':

                        ln[1] = string.lower(ln[1])

                        if ln[1] == 'yes' or ln[1] == 'true':
                            self.input_file_vars[str(ln[0])] = True
                        elif ln[1] == 'no' or ln[1] == 'false':
                            self.input_file_vars[str(ln[0])] = False
                        else:
                            print "Alert! The option for the 'choice' type variable " \
                                  "in the input file '" + str(ln[0]) + "' is unrecognized. " \
                                  "Please use only Yes/No or True/False as values.\n"

                else:
                    print "Alert! The input file contains an unknown entry. The variable '" \
                          + str(ln[0]) + "' is not an input variable for this model. Check " \
                          " the spelling of the variable name and only use the symbols : and = " \
                            "in variable assignments.\n"

        o.close()
        
        for k,v in self.input_file_vars.items():
            setattr(self, self.get_var_name(k), v)
        
        if self.verbose: print 'Finished reading ' + str(numvars) + ' variables from input file.'

 
        
    def set_defaults(self):
    
    
        self.random_pick = random_pick
        self.random_pick_list = random_pick_list
        self.save_figure = save_figure
    
        for k,v in self._var_default_map.items():
            setattr(self, self._var_name_map[k], v)




    def create_dicts(self):
                                   
        self._input_var_names = self._input_vars.keys()

        self._var_type_map = dict()
        self._var_name_map = dict()
        self._var_default_map = dict()

        for k in self._input_vars.keys():
            self._var_type_map[k] = self._input_vars[k]['type']
            self._var_name_map[k] = self._input_vars[k]['name']
            self._var_default_map[k] = self._input_vars[k]['default']



    def set_constants(self):

        self.g = 9.81   # (gravitation const.)
        
        self.dxn_iwalk = [1,1,0,-1,-1,-1,0,1]
        self.dxn_jwalk = [0,1,1,1,0,-1,-1,-1]
        self.dxn_dist = \
        [sqrt(self.dxn_iwalk[i]**2 + self.dxn_jwalk[i]**2) for i in range(8)]
    
        SQ05 = sqrt(0.5)
        self.dxn_ivec = [0,-SQ05,-1,-SQ05,0,SQ05,1,SQ05]
        self.dxn_jvec = [1,SQ05,0,-SQ05,-1,-SQ05,0,SQ05]

        self.walk_flat = np.array([1, -49, -50, -51, -1, 49, 50, 51])
        self.walk = np.array([[0,1], [-SQ05, SQ05], [-1,0], [-SQ05,-SQ05], 
                              [0,-1], [SQ05,-SQ05], [1,0], [SQ05,SQ05]])
      
      

        
    def create_other_variables(self):
    
        self.set_constants()
    
        self.theta_sand = self.coeff_theta_sand * self.theta_water
        self.theta_mud = self.coeff_theta_mud * self.theta_water
    
        self.U_dep_mud = self.coeff_U_dep_mud * self.u0
        self.U_ero_sand = self.coeff_U_ero_sand * self.u0
        self.U_ero_mud = self.coeff_U_ero_mud * self.u0
    
        self.L0 = int(round(self.L0_meters / self.dx))
        self.N0 = max(3,int(round(self.N0_meters / self.dx)))
    
        self.L = int(round(self.Length/self.dx))        # num cells in x
        self.W = int(round(self.Width/self.dx))         # num cells in y

        self.u_max = 2.0 * self.u0          # maximum allowed flow velocity
    
        self.C0 = self.C0_percent * 1/100                       # sediment concentration

        # (m) critial depth to switch to "dry" node
        self.dry_depth = min(0.1, 0.1*self.h0)
        self.CTR = floor(self.W/2)

        self.gamma = self.g * self.S0 * self.dx / (self.u0**2)

        self.V0 = self.h0 * (self.dx**2)    # (m^3) reference volume (volume to
                                            # fill cell to characteristic depth)

        self.Qw0 = self.u0 * self.h0 * self.N0 * self.dx    # const discharge
                                                            # at inlet        
                                                                                                   
        self.qw0 = self.u0 * self.h0                # water unit input discharge
        self.Qp_water = self.Qw0 / self.Np_water    # volume each water parcel

        self.qs0 = self.qw0 * self.C0               # sed unit discharge

        self.dVs = 0.1 * self.N0**2 * self.V0       # total amount of sed added 
                                                    # to domain per timestep

        self.Qs0 = self.Qw0 * self.C0           # sediment total input discharge
        self.Vp_sed = self.dVs / self.Np_sed    # volume of each sediment parcel
    
        self.itmax = 2 * (self.L + self.W)      # max number of jumps for parcel
        self.dt = self.dVs / self.Qs0           # time step size

        self.omega_flow_iter = 2 / self.itermax
 
        # number of times to repeat topo diffusion
        self.N_crossdiff = int(round(self.dVs / self.V0))
    
        # self.prefix
        self.prefix = self.out_dir
        if self.site_prefix:
            self.prefix += self.site_prefix + '_'
        if self.case_prefix:
            self.prefix += self.case_prefix + '_'



    def create_domain(self):
        '''
        Creates the model domain
        '''

        ##### empty arrays #####

        x, y = np.meshgrid(np.arange(0,self.W), np.arange(0,self.L))
    
        self.cell_type = np.zeros_like(x)
    
        self.eta = np.zeros_like(x).astype(np.float32, copy=False)
        self.stage = np.zeros_like(self.eta)
        self.depth = np.zeros_like(self.eta)

        self.qx = np.zeros_like(self.eta)
        self.qy = np.zeros_like(self.eta)
        self.qxn = np.zeros_like(self.eta)
        self.qyn = np.zeros_like(self.eta)
        self.qwn = np.zeros_like(self.eta)
        self.ux = np.zeros_like(self.eta)
        self.uy = np.zeros_like(self.eta)
        self.uw = np.zeros_like(self.eta)
    
        self.wgt_flat = np.zeros((self.L*self.W,8))

        self.qs = np.zeros_like(self.eta)
        self.Vp_dep_sand = np.zeros_like(self.eta)
        self.Vp_dep_mud = np.zeros_like(self.eta)


        ##### domain #####

        self.cell_type[((y-3)**2 + (x-self.CTR)**2)**(0.5) > self.L-5] = -1     # out
        self.cell_type[:self.L0,:]                                     = 2      # land
    
        channel_inds = int(self.CTR-round(self.N0/2))
        self.cell_type[:self.L0,channel_inds:channel_inds+self.N0]     = 1      # channel

        self.stage = (self.L0-y-1) * self.dx * self.S0
        self.stage[self.cell_type <= 0] = 0.
        self.depth[self.cell_type <= 0] = self.h0
        self.depth[self.cell_type == 1] = self.h0

        self.qx[self.cell_type == 1] = self.qw0
        self.qx[self.cell_type <= 0] = self.qw0 / 5.
        self.qw = (self.qx**2 + self.qy**2)**(0.5)

        self.ux[self.depth>0] = self.qx[self.depth>0] / self.depth[self.depth>0]
        self.uy[self.depth>0] = self.qy[self.depth>0] / self.depth[self.depth>0]
        self.uw[self.depth>0] = self.qw[self.depth>0] / self.depth[self.depth>0]

        self.cell_type[self.cell_type == 2] = -2   # reset the land cell_type to -2
    
        self.inlet = list(np.unique(np.where(self.cell_type == 1)[1]))
        self.eta = self.stage - self.depth
