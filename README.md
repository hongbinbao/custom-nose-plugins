custom-nose-plugins
===================
2 plugins for the python nose testing framework: plan-loader and file-output

### Dependcy
    $pip install uiautomatorplug
    
https://github.com/hongbinbao/uiautomatorplug

### Installation
    $pip install customnoseplugins

#### plan-loader
generate test suites with the expected order defined in "plan" file:
    
    $nosetests --with-plan-loader --plan-file PATH_OF_PLAN_FILE --loop INTEGER_NUMBER 

#### file-output
output test result including result, snapshot and log of device into "result.txt"
    
    $nosetests --with-file-output 

#### plan-loader && file-output  
    $nosetests --with-plan-loader --plan-file path_of_plan --loop number --with-file-output --verbosity 2
