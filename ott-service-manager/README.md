# OTT Service Manager

## Description
The ott_service_manager.py script allows, from a configuration file, to set up an OTT configuration on NEA-DVR equipment: Creation of SA/SAF, channels, nPVR and VOD.

## Create your config file

A configuration example file is available here :

`./config/example-config.json` 

### SAF parameters

~~~bash
"saf": {
        "saf_name_1": {
            "streamAdaptations": [
                <A list of names of stream adaptations applied on content.>   
            ]
        },

        ...

        "saf_name_2": {
            "streamAdaptations": [
               <A list of names of stream adaptations applied on content.> 
            ]
        }
    }
~~~

`streamAdaptation` parameter specification are here : [streamAdaptation](https://doc-rd.anevia.com/files/extract/soap-ott/master/ref-profiles.html#streamadaptations)

### SA parameters

~~~bash
"sa": {
        "sa_name_1": {
            "outputFormat": "cmaf",
            "subtitlesFormat": "imsc1",
            "chunkDuration": 2,
            "scramblingType": "cpix"
            ...
        },

        ...

        "sa_name_2": {
            "outputFormat": "dash",
            "mpdTemplateType": "time",
            "subtitlesFormat": "ttmlpassthrough",
            "chunkDuration": 2,
            "scramblingType": "cpix"
            ...
        }
~~~

Parameters specification for `sa_name_x` is available here : [stream adaptation configuration](https://doc-rd.anevia.com/files/extract/soap-ott/master/ref-profiles.html#stream-adaptation-configuration)


### Live Parameters

~~~bash
"live": {
        "channel_name_1": { 
            "nb_channel": 2, *
            "scrambling": "true", *
            "streamers": { *
                "streamer_lg_1": [
                    1,
                    2,
                    3,
                    4,
                    5
                ]
            },
            "type": "ts-generic", *
            ...
            "options": { *
                < Channel option structure >
            }
        },

        ...

        "channel_name_2": {
            ...
        },

~~~

Parameters specification for channel `options` is available here [Channel options](https://doc-rd.anevia.com/files/extract/soap-ott/master/ref-live.html#channel-options): 


The `streamer_name` section allows you to specify the ports index of the streamer `streamer_name` which will be made available to the channel type.

### Scrambling parameters

~~~bash
"scrambling_conf": {
        "scramblingConf": [
            {
               < A scrambling options map >
            }
        ]
    }
~~~

Parameters specification for scrambling `scramblingConf` is available here [scramblingConf](https://doc-rd.anevia.com/files/extract/soap-ott/master/ref-profiles.html#scrambling-options-map)


### nPVR Parameters

~~~bash
"start_time": "2024-04-08 18:00:00"
~~~

The parameter `start_time` is optional and is used to specify the start time of the nPVR range

If not set, `now` is used instead

## Running the script

Get the help :

~~~bash
./ott_service_manager.py -h
~~~

Clean VODs, nPVRs, Live, SA/SAF and scramnling, then create SA/SAF, Scrambling, channels, nPVRs and VODs :

~~~ bash
./ott_service_manager.py -c all -s all generic-config.json
~~~

Create live channel only (not SA/SAF and scrambling)

~~~ bash
./ott_service_manager.py -s live generic-config.json
~~~

*NB: SA/SAF and scrambling are deleted and created only with `all` option*


To only clean equipments, the script `clean_ott_config.py` can be used :

~~~ bash
./clean_ott_config.py -c all http://nea-dvr-dev.lab1.anevia.com:8080/
~~~