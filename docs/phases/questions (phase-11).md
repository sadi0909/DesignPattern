# Phase 11 — Observer questions (answers)

## A. Pattern

### 1. Intent of Observer


Observer is basically used when one object needs to notify multiple other objects when something happens.

In this project, when something like a new reading or command happens, the `EventBus` sends an event to all the subscribers.

The main benefit is that the service doesn't need to know who is listening. We can add new subscribers later without changing the original service.

### 2. Participants and operations

The main parts are:

- **Subject / Event bus:** `EventBus`, which manages the subscribers.
- **Observer:** The subscriber interface with `handle(event)`.
- **Concrete observers:** `MoistureThresholdSubscriber` and `AlertPersistenceSubscriber`.
- **Events:** `ReadingTaken`, `ThresholdCrossed`, `CommandExecuted` and `ActuatorStateChanged`.
- **Publisher:** `ReadingService` and `CommandService`.

`subscribe()` adds a subscriber, `unsubscribe()` removes it and `publish()` sends the event to all registered subscribers.

### 3. When to use / skip Observer

We should use Observer when one action needs to trigger multiple things. For example, a new reading can trigger an alert, save information or update other parts of the application.

We don't really need it when there is only one listener. A normal method call would be simpler.

Also, if we need guaranteed delivery or strict ordering, a simple in-process EventBus is not enough. Then a message queue or another solution would make more sense.

## B. This phase of the application

### 4. Two domain events and their publishers

`ReadingTaken` is published by `ReadingService.take_reading()` after the reading is saved in database.

`CommandExecuted` is published by `CommandService.submit()` when a command succeeds, gets rejected or fails. `ActuatorStateChanged` is also published after a successful start or stop transition.

The publishers should not directly depend on alert repositories or UI components. Otherwise adding something new, like metrics or WebSocket later, would require changing the original services too.

With EventBus, the service just publishes the event and subscribers handle what happens next.

### 5. What `AlertPersistenceSubscriber` does

`AlertPersistenceSubscriber` listens for events and saves alerts in the database.

For example, when a threshold is crossed, it creates a warning alert. If a command fails, it creates a critical alert.

It also checks if an active alert already exists for that device to avoid creating duplicates.

The alerts are stored in the `alerts` table, so they don't disappear when we refresh the browser. The EventFeed gets them from `/api/alerts` every 5 seconds.

### 6. Why polling and a stub are enough

This phase is mainly about learning Observer, not implementing WebSocket.

Polling is enough to show that events are being published, alerts are saved and the UI can display them.

The `services/realtime.ts` file is only a stub for now. It doesn't actually open a WebSocket connection.

Phase 12 will connect WebSocket to the same EventBus and replace polling with realtime updates.

### 7. Must-demo path

The process works like this:

1. User sends a request to read a sensor.
2. `ReadingService` saves the reading and publishes `ReadingTaken`.
3. `MoistureThresholdSubscriber` checks the moisture value against the zone thresholds.
4. If a threshold is crossed, it publishes `ThresholdCrossed`.
5. `AlertPersistenceSubscriber` saves the alert in database.
6. The EventFeed gets the alert from `/api/alerts` and displays it.

`ReadingService` should not create the alert directly. Its job is to save the reading and publish the event. The subscriber handles the alert part.

## C. Compare, contrast, and scenarios

### 8. Observer vs Facade


Facade makes it easier to call multiple services through one operation. For example, in Phase 7 the overview facade collects location, devices, readings and strategy information for the dashboard.

Observer is different because it notifies multiple subscribers when something happens.

So Facade brings things together for the caller, while Observer sends events to different listeners.


### 9. Observer vs Command

Command represents a request to perform an action, like starting a pump. It can be executed and recorded in command history.

Observer is used to notify other parts of the application after something happens.

For example, `CommandService` executes the command and then publishes `CommandExecuted`. Subscribers can react to that event without the command itself knowing anything about alerts.

So Command handles the action, while Observer handles the notifications after it.

### 10. One subscriber throwing during publish

If one subscriber fails and we don't handle the exception, the remaining subscribers might never receive the event.

For example, if the alert subscriber has a bug, it could stop metrics or the future WebSocket subscriber from receiving the same event.

In this project, `EventBus.publish()` uses `try/except` around each subscriber. So if one fails, it logs the error and continues with the others.

This way one subscriber failing doesn't stop the entire process or make the original HTTP request fail.
