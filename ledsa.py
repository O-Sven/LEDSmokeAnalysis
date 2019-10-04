#!/usr/bin/env python

import argparse
import numpy as np
import matplotlib.pyplot as plt

import led_helper as led
import ledsa_conf as lc


class LEDSA:
    
    def __init__(self, load_config_file=True):
        self.config = lc.ConfigData(load_data=load_config_file)
            
        # declarations of global variables
        # 2D numpy array wit dimension (# of LEDs) x (LED_id, x, y)
        self.search_areas = None
        # 2D list with dimension (# of LED arrays) x (# of LEDs per array)
        self.line_indices = None
    """
    ------------------------------------
    LED area search
    ------------------------------------
    """
    
    """finds all LEDs in a single image file and defines the search areas, in
    which future LEDs will be searched"""
    def find_search_areas(self, img_filename):
        config = self.config['find_search_areas']
        filename = "{}{}".format(config['img_directory'], img_filename)
        out_filename = 'led_search_areas.csv'
        
        data = led.read_file(filename, channel=0)
        self.search_areas = led.find_search_areas(data, skip=1, window_radius=int(config['window_radius']))
      
        np.savetxt(out_filename, self.search_areas, delimiter=',',
                   header='LED id, pixel position x, pixel position y', fmt='%d')

    """loads the search areas from the csv file"""    
    def load_search_areas(self):
        filename = 'led_search_areas.csv'
        self.search_areas = led.load_file(filename, delim=',')

    """plots the search areas with their labels"""    
    def plot_search_areas(self, img_filename):
        config = self.config['find_search_areas']
        if self.search_areas is None:
            self.load_search_areas()
        
        filename = "{}{}".format(config['img_directory'], img_filename)
        data = led.read_file(filename, channel=0)
            
        plt.figure(dpi=1200)
        ax = plt.gca()

        for i in range(self.search_areas.shape[0]):
            ax.add_patch(plt.Circle((self.search_areas[i, 2], self.search_areas[i, 1]),
                                    radius=int(config['window_radius']),
                                    color='Red', fill=False, alpha=0.25,
                                    linewidth=0.1))
            ax.text(self.search_areas[i, 2] + int(config['window_radius']),
                    self.search_areas[i, 1] + int(config['window_radius'])//2,
                    '{}'.format(self.search_areas[i, 0]), fontsize=1)
        
        plt.imshow(data, cmap='Greys')
        plt.colorbar()
        plt.savefig('led_search_areas.plot.pdf')

    """
    ------------------------------------
    LED array analysis
    ------------------------------------
    """

    """analyses, which LED belongs to which LED line array"""
    def analyse_positions(self):       
        if self.search_areas is None:
            self.load_search_areas()
        self.line_indices = led.analyse_position_man(self.search_areas, self.config)
                       
        # save the labeled LEDs
        for i in range(len(self.line_indices)):
            out_file = open('line_indices_{:03}.csv'.format(i), 'w')
            for iled in self.line_indices[i]:
                out_file.write('{}\n'.format(iled))
            out_file.close()
            
    """loads the search areas from the csv file"""    
    def load_line_indices(self):
        self.line_indices = []
        for i in range(int(self.config['DEFAULT']['num_of_arrays'])):
            filename = 'line_indices_{:03}.csv'.format(i)
            self.line_indices.append(led.load_file(filename, type='int'))
            
    """plot the labeled LEDs"""        
    def plot_lines(self):
        # plot the labeled LEDs
        if self.line_indices is None:
            self.load_line_indices()
        if self.search_areas is None:
            self.load_search_areas()
        for i in range(len(self.line_indices)):
            plt.scatter(self.search_areas[self.line_indices[i], 2],
                        self.search_areas[self.line_indices[i], 1],
                        s=0.1, label='led strip {}'.format(i))
        
        plt.legend()
        plt.savefig('led_lines.pdf')
        
    """
    ------------------------------------
    LED smoke analysis
    ------------------------------------
    """
    
    """process the image data to find the changes in light intensity"""
    def process_image_data(self):
        config = self.config['analyse_photo']
        if self.search_areas is None:
            self.load_search_areas() 
        if self.line_indices is None:
            self.load_line_indices()  
        data_indices = [7460 + 50*i for i in range(10)]           
    
        if config.getboolean('multicore_processing'):
            from multiprocessing import Pool
    
            with Pool(int(config.num_of_cores)) as p:
                p.map(self.process_file, data_indices)
        else:
            for i in range(len(data_indices)):
                led.process_file(data_indices[i], self.search_areas, self.line_indices, config)
                print('image ', i+1, '/', len(data_indices)+1, ' processed')

    """workaround for pool map"""
    def process_file(self, data_indices):
        led.process_file(data_indices, self.search_areas, self.line_indices, self.config)

    """
    -----------------------------------------
    usefull functions from the helper module
    -----------------------------------------
    """

    def shell_in_ingore_indices(self):
        led.shell_in_ingore_indices()
        
    def shell_in_line_edge_indices(self):
        led.shell_in_line_edge_indices(self.config)


"""
------------------------------------
Default script
------------------------------------
"""
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=
                                     'Allows the analysis of light dampening of LEDs behind a smoke screen.')
    parser.add_argument('--s1', '-s1', '--find_search_areas', action='store_true',
                        help='STEP1: analyse a reference image to find the LED positions and their labels')
    parser.add_argument('--s2', '-s2', '--analyse_positions', action='store_true',
                        help='STEP2: finds the LED array to which each LED belongs')
    parser.add_argument('--s3', '-s3', '--analyse_photo', action='store_true',
                        help='STEP3: finds the changes in light intensity')
    parser.add_argument('--config', '-c', nargs='*', default=None,
                        help='creates the default configuration file. optional arguments are are: img_directory, '
                             'reference_img, number_of_cores. ')
    args = parser.parse_args()

    print(args)

    if args.config is not None:
        if len(args.config) == 0:
            lc.ConfigData()
        if len(args.config) == 1:
            lc.ConfigData(img_directory=args.config[0])
        if len(args.config) == 2:
            lc.ConfigData(img_directory=args.config[0], reference_img=args.config[1])
        if len(args.config) == 3:
            lc.ConfigData(img_directory=args.config[0], reference_img=args.config[1],
                          multicore_processing=True, num_of_cores=args.config[2])
    if args.s1 or args.s2 or args.s3:
        ledsa = LEDSA()
    if args.s1:
        ledsa.find_search_areas(ledsa.config['find_search_areas']['reference_img'])
        ledsa.plot_search_areas(ledsa.config['find_search_areas']['reference_img'])
    if args.s2:
        ledsa.analyse_positions()
        ledsa.plot_lines()
    if args.s3:
        ledsa.process_image_data()
