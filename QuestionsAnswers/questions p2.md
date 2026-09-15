# Phase 2 — Factory Method questions

**Pattern / focus:** Factory Method.


## A. Pattern

1. State the intent of Factory Method in plain language. What problem appears when callers scatter `new` / constructors (or a growing `if type == ...`) across the application?


Ans: Factory Method is a design pattern that helps with creating objects without making the main application directly responsible for knowing how every type of object should be created.

For example, if we have different types of sensors, we do not want the service to have a lot of if/elif statements for creating each sensor. Instead, we can have different creators that know how to create their own type of sensor.

So basically, the caller asks for a sensor, and the creator decides which concrete sensor should be created and what configuration it should have.

The main benefit is that when we add another sensor type later, we do not have to keep changing the main service and adding more conditions to it.



2. Name the main participants of Factory Method (**product**, **concrete product**, **creator**, **concrete creator**, **client**). For each, give one sentence: what it is responsible for.

Ans: There are a few main parts in Factory Method:

Product — The common object that the application wants to create. In our case, it is the Sensor.
Concrete Product — The specific variation of that product, such as a moisture sensor or light sensor.
Creator — The abstraction that defines the factory method. In our case, SensorCreator has create_sensor().
Concrete Creator — The specific creator that knows how to create one type of product, such as MoistureSensorCreator or LightSensorCreator.
Client — The part of the application that asks the creator for the product. Here, SensorService is the main client.

The important part is that the client does not need to know all the construction details of every sensor. It uses the creator instead.



3. How do you add a **new product variant** when creators are polymorphic (new class + registry entry) versus when creation lives in one shared `if/elif` function? Why does that difference matter for extension?


Ans: If we want to add another sensor type, we would create the new sensor behavior, create a corresponding creator for it, and then register that creator with a new key.

The existing SensorService can still call the same create_sensor() method. We do not have to go into the service and add another if/elif branch every time.

For example, if we add a temperature sensor, we could create a TemperatureSensorCreator and register it under something like "temperature".

This is useful because the creation process becomes easier to extend. Instead of modifying one big function every time, we add another creator.

But I would not say this means Factory Method should always be used. If there are only one or two types and the problem is very small and stable, a simple factory could be enough.



## B. This phase of the application

4. In this lab, what is the **product** and what are the **concrete creators**? Why must the API handler (or sensor service) go through a creator/registry instead of constructing `MoistureSensor` / `LightSensor` itself?


Ans: The product in this phase is the plain Python Sensor entity inside the domain layer.

The concrete creators are MoistureSensorCreator and LightSensorCreator. Each one has its own create_sensor() method and is responsible for the defaults of that sensor type.

For example, the moisture creator creates a sensor with device_type="moisture_sensor" and its moisture-specific configuration. The light creator does the same thing for the light sensor.

The API or service should use the creator registry instead of directly constructing these sensors because the creator is the place where the creation rules belong.

The flow is basically:

API router → SensorService → get_creator() → concrete creator → Sensor

So the API does not need to know how every sensor is constructed.




5. `POST /api/sensors` accepts a short `type` key such as `"moisture"` or `"light"`, while the stored/returned field is `device_type` (for example `moisture_sensor`). Why are those two fields different? Who decides the stored `device_type` and `default_config`?

Ans: type is basically the short value that comes from the client when it is making the request. For example:

"moisture"
"light"

It is mainly used to decide which creator should be selected.

device_type is different because it is the proper domain/database value of the actual device. For example:

"moisture_sensor"
"light_sensor"

So I would say type is used for selecting the creator, while device_type represents what the actual saved device is.

The concrete creator should decide the device_type and its default configuration instead of making the API repeat those rules.




6. Why is there a single `devices` table with `role="sensor"` instead of a dedicated `sensors` table? What later phase does that choice prepare for?

Ans: The project uses one general devices table because sensors are just one type of device.

The role field tells us what role that particular device has, and in this phase the sensors are stored with:

role = "sensor"

I think this is useful because we do not need to create a completely separate table for every type of device at the beginning.

For example, later when actuators and other device families are introduced, they can still use the same common device structure instead of forcing us to replace the whole database design.

It does not mean that actuator functionality already exists in Phase 2. It just means that the current design leaves room for those later additions.



7. What should happen when the client posts an **unknown** `type`? Where should that rejection be decided (registry/service vs router constructing a concrete class anyway)?

Ans: If the client sends a sensor type that does not exist, the request should be rejected with an HTTP 400 error before anything is inserted into the database.

The creator registry checks whether a creator exists for that type. If it does not, get_creator() raises a ValueError.

Then the application or API layer catches that error and converts it into a proper HTTP 400 response.

This is better than putting a huge if/elif construction inside the router because the registry is already responsible for knowing which creators are supported.

So the router can stay simple and mainly deal with HTTP, while the creator system deals with choosing the correct creator.




## C. Compare, contrast, and scenarios

8. Contrast Factory Method with a **simple factory** (one function full of `if type == ...`). When is the simple factory “good enough,” and why does this phase still want polymorphic creators?

Ans: A simple factory is usually one function that looks at a type and then uses something like an if/elif statement to decide which object to create.

For example:

if type == "moisture":
    create moisture sensor
elif type == "light":
    create light sensor

This is actually fine when the problem is small and there are only a few stable types.

Factory Method separates that responsibility into different creators. Each creator knows how to create one type of product.

The biggest difference appears when the application grows. With a simple factory, adding a new type usually means going back and modifying the same central function. With Factory Method, we can add another creator and register it while keeping the main service workflow mostly unchanged.

So the simple factory is not wrong. It is just a different level of complexity, and Factory Method gives us a better extension point when we expect the number of variants to grow.




9. Contrast Factory Method with **Abstract Factory** (Phase 3). Factory Method answers which question? Abstract Factory answers which different question? Why is Factory Method enough for Phase 2 sensors?

Ans: Factory Method is mainly about creating one product or one variation of a product.

For example, in this phase, we want to create either a moisture sensor or a light sensor.

Abstract Factory is more about creating a family of related products that should work together.

For example, we could have a factory for a certain device family that creates both a compatible sensor and a compatible actuator.

So I would think of it like this:

Factory Method → Which single product should I create?
Abstract Factory → Which related family of products should I create together?

Factory Method is enough for Phase 2 because we are creating one sensor at a time and do not yet need a whole family of related products.



10. A classmate puts SQLAlchemy session commits (or FastAPI request parsing) **inside** a concrete creator. Why is that a trap? Where should persistence and HTTP stay instead?


Ans: A creator should mainly be responsible for creating and configuring the domain object. It should not also be responsible for HTTP or database operations.

For example, the creator should not parse a FastAPI request, choose an HTTP status code, open a database session, or commit a SQL transaction.

If we put those things inside the creator, then the domain code becomes connected to FastAPI and SQLAlchemy. That makes the code harder to test and also mixes different responsibilities together.

The responsibilities should stay separated:

API layer handles HTTP requests and responses.
Application layer coordinates the use case.
Domain layer contains the sensor and creator rules.
Infrastructure layer handles the database, sessions, queries, and commits.

So in our project, the creator returns a normal Sensor object, and then DeviceRepository converts that into a database row and handles the commit.

This makes each layer responsible for its own job instead of putting everything into the creator.

