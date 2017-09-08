==================
Acquisition Window
==================
The program was inspired by a program known as livefft, written in pyqt4, 
by Dr Rick Lupton (CUED). The livefft program is under the MIT license.

	The MIT License (MIT)																										  	
																																				
	Copyright (c) 2013 rcl33																										
																																				
	Permission is hereby granted, free of charge, to any person obtaining a copy of						  	
	this software and associated documentation files (the "Software"), to deal in							  	
	the Software without restriction, including without limitation the rights to									
	use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of						  	
	the Software, and to permit persons to whom the Software is furnished to do so,						
	subject to the following conditions:																						  	
																																				
	The above copyright notice and this permission notice shall be included in all							  	
	copies or substantial portions of the Software.																		  	
																																				
	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR		  	
	IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS	
	FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR	
	COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER	
	IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN				
	CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.    	
Window Layout
-------------
To be consistent with the analysis window layout, the acquisition window adopts a similar style of layout to the analysis window.
On the left contains the tools to toggle plots, to configure plots, and to configure recording device. In the middle, there are the plots
of the stream in time domain and frequency domain, with a status at the bottom. On the right contains the recording settings and the
plot of the channel levels.

.. autoclass:: cued_datalogger.acquisition_window.LiveplotApp
  :members: