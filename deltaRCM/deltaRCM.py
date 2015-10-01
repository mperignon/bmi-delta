import deltaRCM_base









class DeltaRCM(deltaRCM_base.Tools):

    """
    
    Build deltas from random walks
    
    """
    
    def __init__(self):
        '''
        Creates a new delta model
        '''
        
        self._time = 0.
        self._time_step = 1.
        self.verbose = False
        self.input_file = 'DeltaRCM.in'
        self.Np_water = 0
        self.create_dicts()
        self.set_defaults()
        self.import_file()
        
        self.create_other_variables()
        self.create_domain()
        
        
        
    






    @property
    def time(self):
        """Current model time."""
        return self._time
        
    @property
    def time_step(self):
        """Model time step."""
        return self._time_step

    @time_step.setter
    def time_step(self, time_step):
        """Set model time step."""
        self._time_step = time_step
        
        
        
        

    @property
    def Parcels_water(self):
        """Temperature of the plate."""
        return self.Np_water

    @Parcels_water.setter
    def Parcels_water(self, new_np):
        """Set the temperature of the plate.

        Parameters
        ----------
        new_temp : array_like
            The new temperatures.
        """
        self.Np_water = new_np



# 
# 
#     @property
#     def spacing(self):
#         """Shape of the model grid."""
#         return self._spacing
# 
#     @property
#     def origin(self):
#         """Origin coordinates of the model grid."""
#         return self._origin
# 
#     @classmethod
#     def from_file_like(cls, file_like):
#         """Create a Heat object from a file-like object.
# 
#         Parameters
#         ----------
#         file_like : file_like
#             Input parameter file.
# 
#         Returns
#         -------
#         Heat
#             A new instance of a Heat object.
#         """
#         config = yaml.load(file_like)
#         return cls(**config)




    def advance_in_time(self):
        """Calculate new temperatures for the next time step."""
        
        self.run_one_timestep(self._time)
        self.output_data(self._time)

        self._time += self._time_step


    
    #############################################
    ############# run_one_timestep ##############
    #############################################

    def run_one_timestep(self, timestep):
        '''
        Run the time loop once
        '''

        if self.verbose: print '-'*20
        print 'Time = ' + str(timestep) + ' of ' + str(self.n_steps)


        for iteration in range(self.itermax):

            self.init_water_iteration()
            self.run_water_iteration()

            if timestep>0:
                self.get_profiles()

            self.finalize_water_iteration(timestep, iteration)

        self.init_sed_timestep()

        self.one_coarse_timestep()
        self.one_fine_timestep()

        self.finalize_sed_timestep()


