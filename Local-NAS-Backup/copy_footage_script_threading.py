##################################################################################
# Copyright (c) 2021 Rhombus Systems                                              #
#                                                                                 #
# Permission is hereby granted, free of charge, to any person obtaining a copy    #
# of this software and associated documentation files (the "Software"), to deal   #
# in the Software without restriction, including without limitation the rights    #
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell       #
# copies of the Software, and to permit persons to whom the Software is           #
# furnished to do so, subject to the following conditions:                        #
#                                                                                 #
# The above copyright notice and this permission notice shall be included in all  #
# copies or substantial portions of the Software.                                 #
#                                                                                 #
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR      #
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,        #
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE     #
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER          #
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,   #
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE   #
# SOFTWARE.                                                                       #
###################################################################################
import argparse
import json
import sys
from datetime import datetime, timedelta
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict
import ffmpeg
import os

import requests
import urllib3

import rhombus_logging

# just to prevent unnecessary logging since we are not verifying the host
from rhombus_mpd_info import RhombusMPDInfo

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_logger = rhombus_logging.get_logger("rhombus.CopyFootageToLocalStorage")

URI_FILE_ENDINGS = ["clip.mpd", "file.mpd"]


def init_argument_parser():
    parser = argparse.ArgumentParser(
        description="Pulls footage from a camera on LAN and stores it to the filesystem."
    )
    parser.add_argument(
        "--api_key", "-a", type=str, required=True, help="Rhombus API key"
    )
    parser.add_argument(
        "--cert", "-c", type=str, required=False, help="Path to API cert"
    )
    parser.add_argument(
        "--private_key", "-p", type=str, required=False, help="Path to API private key"
    )
    parser.add_argument(
        "--start_time",
        "-s",
        type=int,
        required=False,
        help="Start time in epoch seconds",
        default=int((datetime.now() - timedelta(hours=1)).timestamp()),
    )
    parser.add_argument(
        "--duration",
        "-u",
        type=int,
        required=False,
        help="Duration in seconds",
        default=1 * 60 * 60,
    )
    parser.add_argument(
        "--debug", "-g", required=False, action="store_true", help="Print debug logging"
    )
    parser.add_argument(
        "--usewan",
        "-w",
        required=False,
        help="Use a WAN connection to download rather than a LAN connection",
        action="store_true",
    )
    parser.add_argument(
        "--location_uuid", "-loc", type=str, required=False, help="Location UUID"
    )
    parser.add_argument(
        "--camera_uuid", "-cam", type=str, required=False, help="Camera UUID"
    )
    parser.add_argument("--destination", "-d", type=str, required=False, help="The destination path to write the ouput file(s) to", default="./")
    return parser


def get_segment_uri(mpd_uri, segment_name):
    for ending in URI_FILE_ENDINGS:
        if ending in mpd_uri:
            return mpd_uri.replace(ending, segment_name)
    return None


def get_segment_uri_index(rhombus_mpd_info, mpd_uri, index):
    segment_name = rhombus_mpd_info.segment_pattern.replace(
        "$Number$", str(index + rhombus_mpd_info.start_index)
    )
    return get_segment_uri(mpd_uri, segment_name)


# This method gets the uuids of cameras and pairs them with any associated audio device

def get_camera_to_gateway_map(api_key, location_uuid=None, camera_uuid=None):
    url_cam = "https://api2.rhombussystems.com/api/camera/getMinimalCameraStateList"
    url_aud = "https://api2.rhombussystems.com/api/audiogateway/getMinimalAudioGatewayStateList"

    # camUuid : {name : camera name, audioGatewayUuid : uuid}
    camUuidDict = {}

    headers = {
        "accept": "application/json",
        "x-auth-scheme": "api-token",
        "content-type": "application/json",
        "x-auth-apikey": api_key,
    }
    body = {}

    response = requests.post(url_cam, headers=headers, json=body)
    camResDict = json.loads(response.text)

    response = requests.post(url_aud, headers=headers, json=body)
    audResDict = json.loads(response.text)

    # if there is a args_main.location_uuid in the argument then filter out and only add cameraUuids to the uuid_lst that have the same locationUuid

    for cam in camResDict["cameraStates"]:
        if cam["connectionStatus"] == "RED":
            continue
        camNameDict = {"name": cam["name"]}

        if location_uuid is not None and cam["locationUuid"] != location_uuid:
            continue
        if camera_uuid is not None and cam["uuid"] != camera_uuid:
            continue

        camUuidDict[cam["uuid"]] = camNameDict

        for audioGateway in audResDict["audioGatewayStates"]:
            for cameraUuid in audioGateway["associatedCameras"]:
                if cameraUuid in camUuidDict:
                    camUuidDict[cameraUuid]["audioGatewayUuid"] = audioGateway["uuid"]

    print("  ---------------------- camUuidDict")
    print(camUuidDict)

    return camUuidDict


class CopyFootageToLocalStorage:
    def __init__(self, args: Dict[any, any], cam: str, video_file_name: str, audio_file_name: str):
        # If debug flag is set, enable logging at DEBUG level
        if args.debug:
            _logger.setLevel("DEBUG")

        # Initialize object variables
        self.api_url = "https://api2.rhombussystems.com"
        self.device_id = cam
        self.video = video_file_name
        self.audio = audio_file_name
        self.use_wan = args.usewan
        self.destination = args.destination

        # Set start_time and duration from arguments, default is handled in argument definition
        self.start_time = args.start_time
        self.duration = args.duration

        # Initialize API and media sessions
        self.api_sess = requests.session()
        self.api_sess.verify = False
        self.media_sess = requests.session()
        self.media_sess.verify = False

        # Set authentication headers based on arguments
        if args.cert and args.private_key:
            scheme = "api"
            self.api_sess.cert = (args.cert, args.private_key)
        else:
            scheme = "api-token"
        self.api_sess.headers = {"x-auth-scheme": scheme, "x-auth-apikey": args.api_key}
        self.media_sess.headers = {
            "x-auth-scheme": scheme,
            "x-auth-apikey": args.api_key,
        }

    def execute_video(self):
        # get a federated session token for media that lasts 1 hour
        session_req_payload = {"durationSec": 60 * 60}
        session_req_resp = self.api_sess.post(
            self.api_url + "/api/org/generateFederatedSessionToken",
            json=session_req_payload,
        )
        _logger.debug("Federated session token response: %s", session_req_resp.content)

        if session_req_resp.status_code != 200:
            _logger.warn(
                "Failed to retrieve federated session token, cannot continue: %s",
                session_req_resp.content,
            )
            return

        federated_session_token = session_req_resp.json()["federatedSessionToken"]
        session_req_resp.close()

        _logger.debug("  ---------------------- before getMediaUris ")
        # get camera media uris
        media_uri_payload = {"cameraUuid": self.device_id}
        media_uri_resp = self.api_sess.post(
            self.api_url + "/api/camera/getMediaUris", json=media_uri_payload
        )
        _logger.debug("Camera media uri response: %s", media_uri_resp.content)

        if session_req_resp.status_code != 200:
            _logger.warn(
                "Failed to retrieve camera media uris, cannot continue: %s",
                media_uri_resp.content,
            )
            return

        mpd_uri_template = (
            media_uri_resp.json()["wanVodMpdUriTemplate"]
            if self.use_wan
            else media_uri_resp.json()["lanVodMpdUrisTemplates"][0]
        )

        _logger.debug("Raw mpd uri template: %s", mpd_uri_template)
        media_uri_resp.close()

        """ 
        When we make requests to the camera, the camera will use our session information to serve the correct files.
        The MPD document call starts the session and tells the camera the start time and duration of the clip requested
        We then get the seg_init.mp4 file which has the appropriate mp4 headers/init data
        and then we get the actual video segment files, named seg_1.m4v, seg_2.m4v, where each segment is a 2 second
        segment of video, so we need to go up to seg_<duration/2>.m4v.  The camera will automatically send the correct
        absolute time segments for each of the clip segments.  Concatenating the seg_init.mp4 and seg_#.m4v files into 
        a single .mp4 gives the playable video.
        """

        # the template has placeholders for where the clip start time and duration are supposed to go, so put the
        # desired start time and duration in the template
        mpd_uri = mpd_uri_template.replace(
            "{START_TIME}", str(self.start_time)
        ).replace("{DURATION}", str(self.duration))
        _logger.debug(" ---------------------- Mpd uri: %s", mpd_uri)

        # use the federated session token as our session id for the camera to process our requests
        media_headers = {"Cookie": "RSESSIONID=RFT:" + str(federated_session_token)}

        # start media session with camera by requesting the MPD file
        mpd_doc_resp = self.media_sess.get(mpd_uri, headers=media_headers)
        _logger.debug("Mpd doc: %s", mpd_doc_resp.content)
        mpd_info = RhombusMPDInfo(str(mpd_doc_resp.content, "utf-8"), False)
        mpd_doc_resp.close()

        # start writing the video stream 
        output_file_path = os.path.join(self.destination, self.video)
        _logger.debug("Will write to: %s", output_file_path)
        with open(output_file_path, "wb") as output_fp:
            # first write the init file
            init_seg_uri = get_segment_uri(mpd_uri, mpd_info.init_string)
            _logger.debug("Init segment uri: %s", init_seg_uri)

            init_seg_resp = self.media_sess.get(init_seg_uri, headers=media_headers)
            _logger.debug("seg_init_resp: %s", init_seg_resp)

            output_fp.write(init_seg_resp.content)
            output_fp.flush()
            init_seg_resp.close()

            # now write the actual video segment files.
            # Each segment is 2 seconds, so we have a total of duration / 2 segments to download
            for cur_seg in range(int(self.duration / 2)):
                seg_uri = get_segment_uri_index(mpd_info, mpd_uri, cur_seg)
                _logger.debug("Segment uri: %s", seg_uri)

                seg_resp = self.media_sess.get(seg_uri, headers=media_headers)
                _logger.debug("seg_resp: %s", seg_resp)

                output_fp.write(seg_resp.content)
                output_fp.flush()
                seg_resp.close()

                # log every 10 minutes of footage downloaded
                if cur_seg > 0 and cur_seg % 300 == 0:
                    _logger.info(
                        "Segments written from [%s] - [%s]",
                        datetime.fromtimestamp(
                            self.start_time + ((cur_seg - 300) * 2)
                        ).strftime("%c"),
                        datetime.fromtimestamp(
                            self.start_time + (cur_seg * 2)
                        ).strftime("%c"),
                    )

        _logger.info(
            "Succesfully downloaded video from [%s] - [%s] to %s",
            datetime.fromtimestamp(self.start_time).strftime("%c"),
            datetime.fromtimestamp(self.start_time + self.duration).strftime("%c"),
            self.video,
        )

    def execute_audio(self, audioGatewayUuid):
        # get a federated session token for media that lasts 1 hour
        session_req_payload = {"durationSec": 60 * 60}
        session_req_resp = self.api_sess.post(self.api_url + "/api/org/generateFederatedSessionToken",
                                              json=session_req_payload)
        _logger.debug("Federated session token response: %s", session_req_resp.content)

        if session_req_resp.status_code != 200:
            _logger.warn("Failed to retrieve federated session token, cannot continue: %s", session_req_resp.content)
            return

        federated_session_token = session_req_resp.json()["federatedSessionToken"]
        session_req_resp.close()

        # get camera media uris
        media_uri_payload = {"gatewayUuid": audioGatewayUuid}
        media_uri_resp = self.api_sess.post(self.api_url + "/api/audiogateway/getMediaUris",
                                            json=media_uri_payload)

        _logger.debug("Audio media uri response: %s", media_uri_resp.content)
        if session_req_resp.status_code != 200:
            _logger.warn("Failed to retrieve audio media uris, cannot continue: %s", media_uri_resp.content)
            return

        if self.use_wan:
            mpd_uri_template = media_uri_resp.json()["wanVodMpdUriTemplate"]
        else:
            mpd_uri_template = media_uri_resp.json()["lanVodMpdUrisTemplates"][0]

        _logger.debug("Raw mpd uri template: %s", mpd_uri_template)
        media_uri_resp.close()

        # the template has placeholders for where the clip start time and duration are supposed to go, so put the
        # desired start time and duration in the template

        # Lets subtract 1 second to equate for 1 second audiostream delay
        mpd_uri = mpd_uri_template.replace("{START_TIME}", str(self.start_time)).replace("{DURATION}",
                                                                                         str(self.duration))
        _logger.debug("Mpd uri: %s", mpd_uri)

        # use the federated session token as our session id for the audio to process our requests
        media_headers = {"Cookie": "RSESSIONID=RFT:" + str(federated_session_token)}

        # start media session with audio by requesting the MPD file
        mpd_doc_resp = self.media_sess.get(mpd_uri, headers=media_headers)
        _logger.debug("Mpd doc: %s", mpd_doc_resp.content)

        print(" ---------------------- before audio mpd_info")
        mpd_info = RhombusMPDInfo(str(mpd_doc_resp.content, 'utf-8'), True)
        print(" ---------------------- after audio mpd_info")
        mpd_doc_resp.close()

        # start writing the audio stream
        # with open(self.audio, "wb") as output_fp: prev line, need to programatically handle audio file name
        print(" ---------------------- before creation of audio_out file")
        with open(self.audio, "wb") as output_fp:
            print(" ---------------------- top of audio_out creation")
            # first write the init file
            init_seg_uri = get_segment_uri(mpd_uri, mpd_info.init_string)
            _logger.debug("Init segment uri: %s", init_seg_uri)

            init_seg_resp = self.media_sess.get(init_seg_uri, headers=media_headers)
            _logger.debug("seg_init_resp: %s", init_seg_resp)

            output_fp.write(init_seg_resp.content)
            output_fp.flush()
            init_seg_resp.close()

            # now write the actual audio segment files.
            # Each segment is 2 seconds, so we have a total of duration / 2 segments to download
            for cur_seg in range(int(self.duration / 2)):
                seg_uri = get_segment_uri_index(mpd_info, mpd_uri,
                                                cur_seg)
                _logger.debug("Segment uri: %s", seg_uri)

                seg_resp = self.media_sess.get(seg_uri, headers=media_headers)
                _logger.debug("seg_resp: %s", seg_resp)

                output_fp.write(seg_resp.content)
                output_fp.flush()
                seg_resp.close()

                # log every 10 minutes of footage downloaded
                if cur_seg > 0 and cur_seg % 300 == 0:
                    _logger.debug("Segments written from [%s] - [%s]",
                                  datetime.fromtimestamp(self.start_time + ((cur_seg - 300) * 2)).strftime('%c'),
                                  datetime.fromtimestamp(self.start_time + (cur_seg * 2)).strftime('%c'))

        _logger.debug("Succesfully downloaded audio from [%s] - [%s] to %s",
                      datetime.fromtimestamp(self.start_time).strftime('%c'),
                      datetime.fromtimestamp(self.start_time + self.duration).strftime('%c'),
                      self.audio)


def worker(camKey, camVal, audioGatewayUuid, args_main):
    time.sleep(0.1)  # introduce a small delay to avoid hitting rate limits
    cam_uuid = camKey
    cam_name = camVal["name"]
    _logger.debug(" ---------------------- saving footage for %s" % cam_name)

    file_type = ".webm" if audioGatewayUuid is not None else ".mp4"

    video_file = (
            "".join(x for x in cam_name if x.isalnum())
            + "_"
            + cam_uuid
            + "_"
            + str(args_main.start_time)
            + "_video"
            + file_type
    )
    print(" ---------------------- audioGatewayUuid %s" % audioGatewayUuid)
    if audioGatewayUuid is not None:
        print(" ---------------------- top of audioGatewayUuid is not None")
        audio_file = (
                "".join(x for x in cam_name if x.isalnum())
                + "_"
                + cam_uuid
                + "_"
                + str(args_main.start_time)
                + "_audio"
                + file_type
        )
        engine = CopyFootageToLocalStorage(args_main, cam_uuid, video_file, audio_file)
        engine.execute_video()
        engine.execute_audio(audioGatewayUuid)
        try:
            input_video = ffmpeg.input(video_file)
            input_audio = ffmpeg.input(audio_file)
            output_file = "".join(x for x in cam_name if x.isalnum()) + "_" + cam_uuid + "_" + str(
                args_main.start_time) + "_videoWithAudio.mp4"
            ffmpeg.concat(input_video, input_audio, v=1, a=1).output(output_file).run(overwrite_output=True)
            os.remove(audio_file)
            os.remove(video_file)
            print(f"Successfully created {output_file} and removed original files.")
        except ffmpeg.Error as e:
            print(f"Error in ffmpeg processing: {e}")
        except Exception as e:
            print(f"Error: {e}")
    else:
        engine = CopyFootageToLocalStorage(args_main, cam_uuid, video_file, None)
        engine.execute_video()


if __name__ == "__main__":
    # this cli command will save the last hour of footage from the specified device
    # python3 copy_footage_to_local_storage.py -a "<API TOKEN>" -d "<DEVICE ID>" -o out.mp4
    t0 = time.time()
    print(" ---------------------- start time %s" % t0)
    arg_parser = init_argument_parser()
    args_main = arg_parser.parse_args(sys.argv[1:])

    camUuidDict = get_camera_to_gateway_map(
        args_main.api_key, args_main.location_uuid, args_main.camera_uuid
    )
    with ThreadPoolExecutor(max_workers=4) as executor:  # limit to 5 concurrent threads
        for camKey, camVal in camUuidDict.items():
            audioGatewayUuid = camVal.get("audioGatewayUuid", None)
            executor.submit(worker, camKey, camVal, audioGatewayUuid, args_main)

    t1 = time.time()
    elapsed_time = t1 - t0
    print(" ---------------------- end time %s" % t1)
    print(
        f" ---------------------- Total execution time: {elapsed_time / 60:.2f} minutes"
    )
