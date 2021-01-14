#!/bin/bash

RESUME_FILE_PFX=".eqi_resume_"

RET_COMPLETED=1
RET_NEW=2

_eqi_basic_clean() {
	echo "Checking for previously uncompleted execution"

    run=$1
    phase=$2

    resume_file="$RESUME_FILE_PFX"${run}_${phase}

    if [[ ! -f "$resume_file" ]]; then
	    echo "Fresh startup, nothing to clean"
    	return $RET_NEW
    fi

	echo "Lock file for the previous task execution found - performing a cleanup"

    while IFS= read -r line;
    do
    	if [[ "$line" == "EQI_COMPLETED" ]]; then # Check if the task is already completed
    	    echo "The task is already completed, we can skip its processing"
    	    return $RET_COMPLETED
    	elif [[ "$line" == "EQI_NO_DIR" ]]; then
    	    if [[ -d "../runs/${run}" ]]; then # Check for run dir that was not present
    	                                   # at the beginning of a task - we should remove it
            	echo "Removing run dir to start from the scratch: ../runs/${run}"
       	        rm -r "../runs/${run}"
        	    return $RET_NEW
            else
                echo "Starting from the scratch, the run dir not existing yet ../runs/${run}"
            	return $RET_NEW
            fi
    	else
    	    break
    	fi
    done < "$resume_file"
}


_eqi_moderate_clean() {

	echo "Checking for possibly broken files from previous execution"

    run=$1
    phase=$2

    resume_file="$RESUME_FILE_PFX"${run}_${phase}
    base_dir="../runs/${run}"

    # Look for changes in run dir, and remove everything what is new
    declare -A locked_files

    while IFS= read -r line;
    do
    	echo "$line"
    	locked_files["$line"]=1
    done < "$resume_file"

    find "$base_dir" -print0 |
    	while IFS= read -r -d '' line; do
	    	if [[ ${locked_files["$line"]} == 1 ]]; then
    			echo "Item locked, keeping it: $line"
    		else
    			if [[ -f "$line" ]]; then
    				echo "File not locked, deleting it: $line"
    				rm "$line"
    			elif [[ -d "$line" ]]; then
    				echo "Dir not locked, deleting it recursively: $line"
    				rm -r "$line"
    			fi
    		fi
    	done
}

eqi_resume_init() {

    if [[ $EQI_RESUME_LEVEL == "DISABLED" ]]; then
        return 0;
    fi

    echo "Initialisation of data for resume in ${EQI_RESUME_LEVEL} level"
    run=$1
    phase="$2"
    base_dir="../runs/${run}"

    echo "Cleaning old task"
    # Check if resume is not disabled, if it is return
    _eqi_basic_clean "${run}" "${phase}"

    # If the task is already completed, return this info to the parent script
    ret_code=$?
    (( ret_code == $RET_COMPLETED )) && return $RET_COMPLETED

    if [[ $EQI_RESUME_LEVEL == "MODERATE" ]]; then
        _eqi_moderate_clean "${run}" "${phase}"
    fi

    echo "Storing initial state of a task"
    if [[ ! -e "$base_dir" ]]; then
        echo "EQI_NO_DIR" > "$RESUME_FILE_PFX"${run}_${phase}
    elif [[ $EQI_RESUME_LEVEL == "MODERATE" ]]; then
        find "$base_dir" > "$RESUME_FILE_PFX"${run}_${phase}
    fi
}

eqi_resume_finish() {

    if [[ $EQI_RESUME_LEVEL == "DISABLED" ]]; then
        return 0;
    fi

    echo "Marking completion of task"

    run=$1
    phase="$2"

    echo "EQI_COMPLETED" > "$RESUME_FILE_PFX"${run}_${phase}
}
