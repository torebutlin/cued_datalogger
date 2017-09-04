#cued_datalogger_addon
addon_metadata = {"name": "Example Addon",
"author": "John Smith",
"category": "Plotting",
"description": "This example draws a sine curve in matplotlib, prints to the console, and draws a sine curve in the time domain window.~This is an extra line~"}

def run(parent_window):
	#------------------------------------------------------------------------------
	# Your addon functions
	#------------------------------------------------------------------------------
	def plot_sine(plot_item, pen):
	    t = np.arange(1e3)/1e4;
	    plot_item.plot(t,np.sin(2*np.pi*1e2*t),pen = 'k')
	
	#--------------------------------------------------------------------------
	# Your addon code:
	#--------------------------------------------------------------------------
	# Addons allow imports
	import matplotlib.pyplot as plt
	import numpy as np
	
	t = np.arange(1e3)/1e4;
	plt.plot(t,np.sin(2*np.pi*1e2*t))
	# Addons allow printing to stdout
	print("Hello World!")
	
	# Addons can access things in the analysis window
	default_pen = parent_window.CurrentWorkspace.default_pen
	time_domain = parent_window.display_tabwidget.widget(0)
	# And can interact with them
	plot_sine(time_domain.plotitem, default_pen)