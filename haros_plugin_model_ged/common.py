# -*- coding: utf-8 -*-

#Copyright (c) 2020 André Santos
#
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#THE SOFTWARE.


###############################################################################
# Constants
###############################################################################

NODE = 1
TOPIC = 2
SERVICE = 3
PARAMETER = 4

RTYPES = {
    NODE: "node",
    TOPIC: "topic",
    SERVICE: "service",
    PARAMETER: "parameter"
}

PUBLISH = 1
SUBSCRIBE = 2
SERVER = 3
CLIENT = 4
GET = 5
SET = 6

LTYPES = {
    PUBLISH: "topic publisher",
    SUBSCRIBE: "topic subscriber",
    SERVER: "service server",
    CLIENT: "service client",
    GET: "parameter reader",
    SET: "parameter writer"
}
