# Transitioning from Callback-based MQTT Client API to an Async I/O Task-based API

## Objective

The primary objective of this change is to enhance error handling mechanisms, particularly for SSL sockets when TLS is enabled for MQTT, by transitioning from the direct usage of the callback-based MQTT client API provided by the Paho library to a task-based implementation utilizing an asynchronous I/O event loop. This transition is motivated by a need to address the challenge of detecting and handling errors effectively, which were previously going unnoticed due to their occurrence in a separate thread running the standard Paho MQTT loop.

## Background

The Paho MQTT client provides a comprehensive framework for MQTT communication. Traditionally, this framework employs a callback-based approach where the client registers callbacks for specific events (e.g., on_connect, on_message). While this method is functional, it has been identified that error handling, especially for SSL sockets in a TLS-enabled MQTT environment, is less effective, leading to unnoticed errors in the thread where the Paho loop was running, and apparently they were not being caught (and it [resulted difficult to bubble them up to the main thread](https://stackoverflow.com/questions/77475685/threading-excepthook-args-exc-traceback-is-none)). By using Paho from an asynchronous event loop, errors don't happen outside the main thread so their handling is guaranteed, while blocking the main code flow is avoided.

Also, the opportunity was identified to move away from the potential [callback-hell](http://callbackhell.com/) situation when directly using Paho's callbacks from the CLI's business logic, by leveraging the linear logic flow provided by the async-await syntax, and Trio's features for [structured](https://vorpus.org/blog/notes-on-structured-concurrency-or-go-statement-considered-harmful/) [concurrency](https://blog.yoshuawuyts.com/tree-structured-concurrency/).


## Rationale

- **Centralized Error Management**: Async I/O allows for centralized error handling mechanisms, making it easier to catch and manage exceptions, especially those related to SSL and TLS operations.

- **Structured Flow**: Asynchronous code using async/await syntax results in a more linear and structured flow, reducing complexity and making the codebase easier to understand and maintain.

- **Clear Error Propagation**: Errors in async/await patterns are propagated clearly and can be handled at the appropriate level of the application, improving the robustness of the system.

- **Graceful Shutdown and Cleanup**: The task-based approach ensures that resources are properly managed and released, even in cases of error or exception, preventing resource leakage.
