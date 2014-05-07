custom-nose-plugins
===================
plugins for the python nose testing framework.
  plan-loader: generate test suites with the expect order defined in "plan" file
  file-output: output test result including result, snapshot and log of device into "result.txt"

* Dependcy:  
    ```
    sudo pip install devicewrapper
    ```

    https://github.com/hongbinbao/devicewrapper

* Install:   
    ```
    sudo pip install customnoseplugins
    ```

* Usage:  

  * plan-loader  
    ```
    nosetests --with-plan-loader --plan-file-name path_of_plan --plan-loop-number number 
    ```  

  * file-output  
    ```
    nosetests --with-file-output 
    ```  

  * plan-loader && file-output  
    ```
    nosetests --with-plan-loader --plan-file-name path_of_plan --plan-loop-number number --with-file-output 
    ```  
