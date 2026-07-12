#!/bin/bash
D=/home/wosas/Desktop/26-1_RPM/Datas/CustomData/0416_Data
L=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/scripts/pipeline/run_scene_pipeline.sh
bash $L 301_1253_rot "$D/0416_301-1253-2_rot/0416_301-1253-2.vrs"
bash $L 301_12F      "$D/0416_301-12F/0416_301-12F.vrs"
bash $L 301_305      "$D/0416_301-305/0416_301-305.vrs"
