# Welcome to Rhombus Systems

Rhombus Systems was built on a foundation of API-driven micro-services. As a result, a deep and comprehensive set of API
endpoints exist and are made available to our customers. These API contracts are not an afterthought, but are actually
used by internal Rhombus software. This means that anything that the system is capable of doing can also be done via the
Rhombus API.

This Repository is home to Python based examples for many of the endpoints of Rhombus Systems' API, examples for other
common languages can be found [here.](https://github.com/RhombusSystems)

To get started and explore the API's
Documentation, [Click Here!](https://developer.rhombus.com/)

For answers to Frequently Asked
Questions, [Click Here!](https://support.rhombussystems.com/hc/en-us/sections/115002570508-FAQ)

# Examples in this Repository

**example_Name.py**

What does this example do?

**API Endpoints**

- Which endpoints does this example use?

**Dependencies**

- Does this example have any external dependencies?

## add_or_remove_labels.py

This example batch modifies labels based on CLAs

#### API Endpoints

- [face/addFaceLabel](https://developer.rhombus.com/api-reference/face-recognition-person-webservice/add-a-label-to-a-person)
- [face/removeFaceLabel](https://developer.rhombus.com/api-reference/face-recognition-person-webservice/remove-a-label-from-a-person)

## climate_create_seekpoint.py

This example gets the rate of change of the temperature.

#### API Endpoints

- [climate/getMinimalClimateStateList](https://developer.rhombus.com/api-reference/climate-webservice/get-minimal-climate-state-list)
- [climate/getClimateEventsForSensor](https://developer.rhombus.com/api-reference/climate-webservice/get-climate-events-for-environmental-sensor)
- [camera/getMinimalCameraStateList](https://developer.rhombus.com/api-reference/camera-webservice/get-minimal-camera-state-list)
- [camera/createFootageSeekpoints](https://developer.rhombus.com/api-reference/camera-webservice/create-custom-footage-seekpoints)

## copy_footage_to_local_storage.py

This example pulls footage from a camera on LAN and stores it to the filesystem.

#### API Endpoints

- [org/generateFederatedSessionToken](https://developer.rhombus.com/api-reference/org-webservice/generate-federated-session-token)
- [camera/getMediaUris](https://developer.rhombus.com/api-reference/camera-webservice/get-camera-media-uris)

## door_report.py

This example gets a report of the recent door openings and closings.

#### API Endpoints

- [location/getLocations](https://developer.rhombus.com/api-reference/location-webservice/get-locations)
- [door/getMinimalDoorStateList](https://developer.rhombus.com/api-reference/door-webservice/get-basic-state-information-for-all-door-sensors)
- [door/getDoorEventsForSensor](https://developer.rhombus.com/api-reference/door-webservice/get-list-of-door-openclose-events-for-door-sensor)

## face_report.py

This example gets a report of the recent faces and downloads the pictures of each face.

#### API Endpoints

- [proximity/getMinimalProximityStateList](https://developer.rhombus.com/api-reference/proximity-webservice/get-minimal-proximity-state-list)
- [face/getRecentFaceEventsV2](https://developer.rhombus.com/api-reference/face-recognition-event-webservice/find-face-events-by-organization)

## get_frame.py

This example pulls a frame from a camera on LAN and saves it.

#### API Endpoints

- [video/getExactFrameUri](https://developer.rhombus.com/api-reference/video-webservice/get-exact-frame-uri)

## licenseplate_report.py

This example gets a report of recent licenseplates and downloads the pictures of each one.

#### API Endpoints

- [camera/getMinimalCameraStateList](https://developer.rhombus.com/api-reference/camera-webservice/get-minimal-camera-state-list)
- [vehicle/getRecentVehicleEvents](https://developer.rhombus.com/api-reference/vehicle-webservice/get-recent-vehicle-events)

## LiveStreamingExample

This example demonstrates how to re-stream Rhombus live camera footage to a web client.

#### API Endpoints

- [camera/getMediaUris](https://developer.rhombus.com/api-reference/camera-webservice/get-camera-media-uris)
- [org/generateFederatedSessionToken](https://developer.rhombus.com/api-reference/org-webservice/generate-federated-session-token)

## tag_filter_stats.py

This example filters through tag movements and creates CSV file..

#### API Endpoints

- [proximity/getMinimalProximityStateList](https://developer.rhombus.com/api-reference/proximity-webservice/get-minimal-proximity-state-list)
- [location/getLocations](https://developer.rhombus.com/api-reference/location-webservice/get-locations)
- [proximity/getLocomotionEventsForTag](https://developer.rhombus.com/api-reference/proximity-webservice/get-locomotion-events-for-tag)

## timelapse_saver.py

This example creates a timelapse and saves it in a file.

#### API Endpoints

- [camera/getMinimalCameraStateList](https://developer.rhombus.com/api-reference/camera-webservice/get-minimal-camera-state-list)
- [video/getTimelapseClips](https://developer.rhombus.com/api-reference/video-webservice/get-timelapse-clips)
- [video/generateTimelapseClip](https://developer.rhombus.com/api-reference/video-webservice/generate-timelapse-clip)

## user_list.py

This example gets a report of all of the Users and their emails.

#### API Endpoints

- [user/getUsersInOrg](https://developer.rhombus.com/api-reference/user-webservice/get-users-in-organization)

## video_clip_report.py

This example creates and downloads a clip and accompanying report.

#### API Endpoints

- [camera/getMinimalCameraStateList](https://developer.rhombus.com/api-reference/camera-webservice/get-minimal-camera-state-list)
- [video/spliceV2](https://developer.rhombus.com/api-reference/video-webservice/splice-v2)
- [event/getClipsWithProgress](https://developer.rhombus.com/api-reference/event-webservice/get-list-of-saved-clips-in-organization-with-current-progress)
- [event/getSavedClipDetails](https://developer.rhombus.com/api-reference/event-webservice/get-detailed-information-about-a-saved-clip-including-seekpoints-and-bounding-boxes)

## webhook.py

This example creates a webhook in the Rhombus console and downloads video footage of notified alerts through the
webhook.

#### API Endpoints

- [org/generateFederatedSessionToken](https://developer.rhombus.com/api-reference/org-webservice/generate-federated-session-token)
- [integrations/updateWebhookIntegration](https://developer.rhombus.com/api-reference/webhook-integrations-webservice/update-webhook-integration)