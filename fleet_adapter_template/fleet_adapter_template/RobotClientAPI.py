# Copyright 2021 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


'''
    The RobotAPI class is a wrapper for API calls to the robot. Here users
    are expected to fill up the implementations of functions which will be used
    by the RobotCommandHandle. For example, if your robot has a REST API, you
    will need to make http request calls to the appropriate endpoints within
    these functions.
'''

import typing
import socketio
import threading

class RobotAPI:
    # The constructor below accepts parameters typically required to submit
    # http requests. Users should modify the constructor as per the
    # requirements of their robot's API
    def __init__(self, 
                prefix: str, user: str, password: str,
                server_url : str, token : str, namespace : str 
        ):

        self.server_url = server_url
        self.token = token
        self.namespace = namespace
        
        self.response_fleet_adapater_data = None
        self.response_fleet_adapater_event = threading.Event()
        self.response_fleet_adapater_event.clear()

        self.sio = socketio.Client( reconnection = False)
        self.sio.on('connect', self._on_connect)
        self.sio.on('connect_error', self._on_connect_error)
        self.sio.on('disconnect', self._on_disconnect)
        self.robot_odom : typing.Dict[str, typing.List[float]]= {
            "pose" : [],
            "twist" : [],
        }
        self.sio.on('receive_odom', self._on_position )

        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

        # Original
        self.prefix = prefix
        self.user = user
        self.password = password
        self.connected = 0
        # Test connectivity
        connected = self.check_connection()
        if connected:
            print("Successfully able to query API server")
            self.connected = 1
        else:
            print("Unable to query API server")

    def check_connection(self):
        print( "RobotClient API call check_connection")
        ''' Return True if connection to the robot API server is successful'''
        # ------------------------ #
        # D - IMPLEMENT YOUR CODE HERE #
        # ------------------------ #
        return self.connected != 1

    def _on_position(self, data ):
        # print('⬇️  Received:', data["x"], data["y"], data["yaw"])
        self.robot_odom = data

    def position(self, robot_name: str):
        # print( "RobotClient API call position")
        if len(self.robot_odom["pose"]) == 0 :
            return None
        else:
            return [self.robot_odom["pose"][0], self.robot_odom["pose"][1], self.robot_odom["pose"][5]]
        ''' Return [x, y, theta] expressed in the robot's coordinate frame or
            None if any errors are encountered'''
        # ------------------------ #
        # D - IMPLEMENT YOUR CODE HERE #
        # ------------------------ #
        return None

    def navigate(self, robot_name: str, pose, map_name: str):
        print( f'RobotClient API call navigate to {pose}' )
        ''' Request the robot to navigate to pose:[x,y,theta] where x, y and
            and theta are in the robot's coordinate convention. This function
            should return True if the robot has accepted the request,
            else False'''
        
        request_data = {
            "type" : "navigate",
            "pose": pose,
            "map": map_name
        }

        self.response_fleet_adapater_event.clear()
        self.sio.emit( "call_fleet_adapter", request_data, callback = self._callback_response_fleet_adapter )

        if self.response_fleet_adapater_event.wait( timeout = 10.0 ):
            print( f'Succeess command navigate : {self.response_fleet_adapater_data}')
            return True
        else:
            print( f'Failure command navigate')
            return False
        # ------------------------ #
        # IMPLEMENT YOUR CODE HERE #
        # ------------------------ #
        return False

    def start_process(self, robot_name: str, process: str, map_name: str):
        print( "RobotClient API call start_process")
        ''' Request the robot to begin a process. This is specific to the robot
            and the use case. For example, load/unload a cart for Deliverybot
            or begin cleaning a zone for a cleaning robot.
            Return True if the robot has accepted the request, else False'''
        return True
        # ------------------------ #
        # IMPLEMENT YOUR CODE HERE #
        # ------------------------ #
        return False

    def stop(self, robot_name: str):
        print( "RobotClient API call stop")
        ''' Command the robot to stop.
            Return True if robot has successfully stopped. Else False'''
        return True
        # ------------------------ #
        # IMPLEMENT YOUR CODE HERE #
        # ------------------------ #
        return False

    def navigation_remaining_duration(self, robot_name: str):
        print( "RobotClient API call navigation_remaining_duration")
        ''' Return the number of seconds remaining for the robot to reach its
            destination'''
        return 10.0
        # ------------------------ #
        # IMPLEMENT YOUR CODE HERE #
        # ------------------------ #
        return 0.0

    def navigation_completed(self, robot_name: str):
        print( "RobotClient API call navigation_completed")
        ''' Return True if the robot has successfully completed its previous
            navigation request. Else False.'''
        # ------------------------ #
        # IMPLEMENT YOUR CODE HERE #
        # ------------------------ #
        return False

    def process_completed(self, robot_name: str):
        print( "RobotClient API call process_completed" )
        ''' Return True if the robot has successfully completed its previous
            process request. Else False.'''
        # ------------------------ #
        # IMPLEMENT YOUR CODE HERE #
        # ------------------------ #
        return False

    def battery_soc(self, robot_name: str):
        print( "RobotClient API call battery_soc" )
        ''' Return the state of charge of the robot as a value between 0.0
            and 1.0. Else return None if any errors are encountered'''
        return 1.0
        # ------------------------ #
        # IMPLEMENT YOUR CODE HERE #
        # ------------------------ #
        return None
    
    def _on_connect(self):
        print(f"✔ Connected to {self.server_url} (sid={self.sio.sid})")
        # Join the namespace with an ack handler
        def ack_handler(resp=None):
            if resp is None:
                print(f"🔗 Joined namespace {self.namespace}")
            else:
                print(f"❌ Join failed: {resp}")

        self.sio.emit('register', self.namespace, callback=ack_handler)
        self.connected = 1

    def _run(self):
        # Pass the JWT as a query string for the initial handshake
        self.sio.connect(self.server_url, auth= { 'token' : self.token } )
        self.sio.wait()

    def _on_connect_error(self, error):
        print(f"❌ Connection error: {error}")
        self.connected = 0

    def _on_disconnect(self):
        print("— Disconnected from server")
        self.connected = 0

    def _callback_response_fleet_adapter(self, data ):
        self.response_fleet_adapater_data = data
        self.response_fleet_adapater_event.set()