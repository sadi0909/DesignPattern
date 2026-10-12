# Phase 5 — Adapter questions

**Pattern / focus:** Adapter.

**Read first:** [Guide 05](../../materials/guides/05-adapter.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example a legacy XML calendar client) as if they were your greenhouse classes.
- When a question asks about *this application*, refer to sensor ports, adapters, readings, and `sensor_readings` from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.

## A. Pattern

1. State the intent of Adapter in plain language. What problem appears when business code speaks a vendor or legacy protocol (odd field names, units, XML, status codes) directly?

Ans:

Adapter is basically used when two things have different interfaces and we want them to work together without rewriting either one.

In this lab the vendor stub gives us data in a different format, like reading_tenths, uom_code and epoch milliseconds, while simulation driver gives more normal values.

If the business code works directly with these different formats, then every place has to know how to parse it, convert the units and timestamps etc. If vendor changes something later, we would have to change the service code also.

With Adapter, we make one small class which translates the vendor data into the format that our application already expects.

2. Name the participants (**target / port**, **adaptee**, **adapter**, **client**). What does the adapter translate, and what must it **not** decide (business policy)?

Ans:

The main parts are:
Target / port: SensorPort and ActuatorPort, which are the interfaces our application expects.
Adaptee: The foreign driver we are trying to use, like the vendor SDK or simulation driver.
Adapter: VendorStubSensorAdapter and SimulationSensorAdapter, which translate the driver into our port.
Client: ReadingService and the sensors router, which only use the port.

The adapter basically translates the data shape and protocol. For example field names, unit conversion, scaling and timestamps.

But it should not decide business rules.

For example if moisture is below 0.3 then water the plant, that is not adapter logic. Thats a business decision and should be handled by Strategy later.

3. GoF distinguishes an **object adapter** (composition) from a **class adapter** (inheritance). Which does modern code prefer, and why?

Ans:

Modern code usually prefer object adapter because it uses composition instead of inheritance.

The adapter wraps the adaptee and implements the interface that our application needs. This makes it more flexible because we can give it different adaptee objects, use stubs for testing and change the wrapped object more easily.

Class adapter uses inheritance and in some languages it needs multiple inheritance. That makes the adapter more tightly connected to one specific adaptee class.

In this lab we are using object adapters. For example VendorStubSensorAdapter.read() wraps the vendor call and then translates the result into our normal format.

## B. This phase of the application

4. What is `SensorPort` in this lab, and what normalized value type (for example `Reading`) do adapters return? Why do application services depend on the port rather than on a simulation driver or vendor SDK?

Ans:

SensorPort is basically the interface that the application uses for reading sensors. It has one main operation:

read(device) -> Reading

The adapters return the same Reading object no matter which driver is used. It contains things like device_id, value, unit, source and recorded_at.

The service depends on SensorPort instead of directly depending on simulation driver or vendor SDK.

This means we can change the driver later without changing the service. For example we can replace the vendor with another one or replace simulation with real hardware and the rest of the application can stay same.

Also the vendor specific imports and data formats stay inside the adapter instead of spreading through the application.

5. You need **at least two** adapters (simulation and a vendor stub) with **different raw shapes** but the same normalized reading. Why is the different raw shape the point of the exercise? How does the `source` field on a reading show which adapter produced it?

Ans:

If both drivers already gave us the same Reading format, then there would be nothing much to adapt.

The point is that the raw data is different.

The vendor stub gives a nested payload like sample.reading_tenths, uses unit codes like PCT and KLX, and gives timestamp as captured_epoch_ms.

The simulation driver gives a more simple value.

But after going through the adapters both of them should become the same Reading object.

The source field tells us where that reading came from. So it can be "simulation" or "vendor". This is also useful in the database because we can see which adapter produced each reading and UI can show the difference.

6. Readings are **appended** to `sensor_readings` (history grows). Why not keep only the latest value in memory or overwrite a single row? Which later phase consumes this history?

Ans:

If we only keep the latest value in memory, then we lose it when the application restart. Also other processes can't use that value and we have no history.

Keeping the readings means we can see how the value changes over time. One reading alone doesn't tell us much. For example if moisture is 0.2, we don't know if it was going down from 0.8 or going up from 0.1.

So the readings are appended to sensor_readings and the history keeps growing.

The table is indexed by (device_id, recorded_at DESC) so getting the latest reading for a device is still fast.

Phase 6 Strategy will use this history for making decisions based on recent readings and zone thresholds. Later Observer can also publish events when a reading is created.

7. `POST /api/sensors/{id}/read` runs an adapter, persists, and returns a DTO. What HTTP status is appropriate when the device is missing versus when the adapter fails? Why must the router never see vendor-shaped types?

Ans:

If the device does not exist, then it should return 404 because the requested resource is missing. This comes from DeviceNotFoundError.

If the device exists but the adapter fails, for example the vendor payload is wrong or has an unknown unit code, then it should return 400 Bad Request using SensorReadError.

When everything works and a new reading is created, 201 is appropriate.

The router should never see the vendor shaped data because that would mean the adapter is not really hiding the vendor system.

If the router has to understand things like reading_tenths or vendor XML, then changing the vendor later means changing the route code too. The whole point of the adapter is to keep these details inside the adapter.
## C. Compare, contrast, and scenarios

8. Contrast Adapter with **Facade**. Adapter changes the **shape** of an existing interface; Facade simplifies **how to use** a subsystem. Give a greenhouse-shaped example of each (Adapter this phase; Facade in Phase 7).

Ans:

Adapter and Facade both can be used as a wrapper, but they solve different problem.

Adapter is used when the interfaces don't match and we need to translate one into another.

Facade is used when the interfaces can already work, but there are many things behind it and we want to give the client one simpler way to use them.

For example in this phase VendorStubSensorAdapter takes the vendor format and makes it look like SensorPort.read() -> Reading. That is Adapter.

A Phase 7 Facade could have something like overview() behind GET /api/overview, which gets devices, latest readings and location configuration from several services in one call.

So Facade is simplifying how we use the subsystem, while Adapter is changing the interface so they can work together.

9. Contrast Adapter with **Decorator**. Both wrap an object. What is different about the interface they present to the client?

Ans:

The main difference is the interface they give to the client.

Adapter gives a different interface from the object it wraps. It translates one interface into another.

Decorator gives the same interface as the object it wraps and only adds some extra behavior.

For example, VendorStubSensorAdapter gives SensorPort.read() even though the vendor underneath has a completely different data format. That is Adapter.

A Decorator later can wrap SimulationActuatorAdapter but still expose ActuatorPort.apply(). It can add things like logging, timing or retries without changing the interface.

10. A classmate puts irrigation policy (“if moisture &lt; 0.3 then water”) inside the vendor adapter. Why is that a trap? Where should that decision live instead (later Strategy), and what should stay in the adapter?

Ans:

It is a trap because the adapter should only translate the driver, not make business decisions.

If we put something like “if moisture < 0.3 then water” inside the vendor adapter, then we are hard coding business logic into infrastructure code.

Also the 0.3 value may not be correct for every zone because Phase 4 lets each zone have its own thresholds.

Then if we have another adapter, like simulation, we would have to copy the same rule there too.

The decision should be handled later by Strategy, where the policy can look at the recent readings and the zone thresholds and decide what action to take.

The adapter should only handle things like field mapping, unit conversion, timestamp conversion and sending the actual command to the driver for actuators.

Basically adapter translates, it shouldnt decide what the system should do.
