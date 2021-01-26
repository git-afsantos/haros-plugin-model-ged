# Model Graph Extraction Difference

This is a HAROS plugin to calculate the Graph Extraction Difference of extracted models against a ground truth.

It should serve little to no purpose for regular HAROS users.
It has been used to evaluate the performance of the HAROS model extractor in terms of Precision, Recall and F1-Score.

In order to use this plugin, you must pass it, as input in the project file, a ground truth of the expected Computation Graph.
That is, you must list every detail of every entity (nodes, topics, services, parameters).
For example:

```yaml
%YAML 1.1
---
project: Fictibot
packages:
  - fictibot_drivers
  - fictibot_controller
  - fictibot_multiplex
  - fictibot_msgs
configurations:
  multiplex:
    launch:
      - fictibot_controller/launch/multiplexer.launch
    user_data:
      haros_plugin_model_ged:
        truth:
          nodes:
            /fictibase:
              node_type: fictibot_drivers/fictibot_driver
              traceability:
                package: fictibot_controller
                file: launch/multiplexer.launch
                line: 2
                column: 3
              publishers:
                - topic: /bumper
                  msg_type: std_msgs/Int8
                  queue_size: 21
                  traceability:
                    package: fictibot_drivers
                    file: src/sensor_manager.cpp
                    line: 10
                    column: 29
                - topic: /laser
                  msg_type: std_msgs/Int8
                  queue_size: 21
                  traceability:
                    package: fictibot_drivers
                    file: src/sensor_manager.cpp
                    line: 11
                    column: 29
                # ...
              subscribers:
                - topic: /stop_cmd
                  msg_type: std_msgs/Empty
                  queue_size: 21
                  traceability:
                    package: fictibot_drivers
                    file: src/motor_manager.cpp
                    line: 15
                    column: 30
                - topic: /teleop_cmd
                  msg_type: std_msgs/Float64
                  queue_size: 21
                  traceability:
                    package: fictibot_drivers
                    file: src/motor_manager.cpp
                    line: 17
                    column: 30
                # ...
```

Then, the plugin compares the automatically extracted model with this ground truth, and reports the final results, including incorrect, missing or spurious entities.
