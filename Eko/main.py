#
#  main.py
#  Eko
#
#  Created by Johan Nordberg on 2009-08-09.
#  Copyright Inveno 2009. All rights reserved.
#

#import modules required by application
import objc
import Foundation
import AppKit

from PyObjCTools import AppHelper

# import modules containing classes required to start application and load MainMenu.nib
import EkoAppDelegate

# pass control to AppKit
AppHelper.runEventLoop()
