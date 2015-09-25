#!/bin/bash
source ../../setup.shell

httk-project-setup tutorial_step6
httk-computer-setup local local
httk-computer-install local
httk-tasks-send-to-computer local Runs/
httk-tasks-start-taskmanager local
