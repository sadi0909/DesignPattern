# Phase 3 — Abstract Factory questions

**Pattern / focus:** Abstract Factory.

**Read first:** [Guide 03](../../materials/guides/03-abstract-factory.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example PDF/HTML export kits) as if they were your greenhouse classes.
- When a question asks about *this application*, refer to device families, provision, and the unified devices API from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.

## A. Pattern

1. State the intent of Abstract Factory in plain language. What goes wrong when related products are chosen independently (`if format` for each piece) instead of as a **family**?
Ans:

Abstract Factory is basically used when we have different products which belongs to same family and they should work together. Instead of choosing every product separately, we choose one factory and that factory will create all the related products.
If we choose every product separately with different if statements, there is a chance we can mix two different families. For example, one sensor can be form simulation and actuator can be from edge. Then the settings or protocol will not match and it can cause problem later.
Also the family selection logic will be in many places in the code. So if we change something we have to find and change many places. With Abstract Factory we choose the family once and factory takes care of the rest.


2. Name the main participants (**abstract factory**, **concrete factory**, **abstract products**, **concrete products**, **client**). How does choosing a factory at the start **commit** the client to one family?
Ans:

The main parts are:
Abstract factory: DeviceFamilyFactory which gives the common factory methods.
Concrete factories: SimulationDeviceFactory and EdgeHardwareFactory.
Abstract products: The common Device type. The role tells if it is sensor or actuator.
Concrete products: Moisture sensor, light sensor, water pump and grow light.
Client: DeviceFamilyService which chooses the family and ask the factory to create the kit.

When client choose one factory, the whole kit comes from that factory. So if we choose edge factory then all the devices will be edge devices.
So client dont have to choose the family again for every single device.


3. When should you use Abstract Factory, and when should you skip it (for example only one product type per request, or mixing siblings is valid)?
Ans:

We should use Abstract Factory when we have more than one type of product and they need to work together as one family.
In this project devices need to belong to same environment, either simulation or edge, so Abstract Factory makes sense here.
We dont really need it when we are only creating one product at a time. Then Factory Method can be enough. Also if mixing different implementations is okay then there is no reason to make a whole family factory.
Basically the pattern should be used when we actually have a consistency problem that it solves.


## B. This phase of the application

4. In this lab, what is a **device family**, and what does `create_device_set()` (or your equivalent) return? Why must a simulation kit and an edge kit not mix incompatible siblings?
Ans:

A device family is basically a group of devices which are made for the same environment.
In this phase there are 2 families:
- simulation
- edge

create_device_set() returns 4 Device objects. 2 sensors which are moisture sensor and light sensor, and 2 actuators which are water pump and grow light.
The simulation devices use sim protocol. The edge devices use gpio-stub and can also have things like GPIO pin settings.
We shouldnt mix them because they are configured for different environment. For example edge actuator can have hardware settings while simulation device is expecting simulation. So if we mix them the kit may not work correctly.


5. Phase 2 Factory Method creators still exist. How does Abstract Factory **compose** them rather than replace them? What would you lose if you deleted the sensor creators and inlined all construction inside the family factory?
Ans:

Phase 2 was mainly for creating one sensor. For example MoistureSensorCreator creates moisture sensor and LightSensorCreator creates light sensor.
Phase 3 is more about choosing the whole family.
So the family factory can use those sensor creators from Phase 2 to create the sensors. Then it adds the family key and protocol and also creates the actuators needed for complete kit.
So Abstract Factory is not replacing Factory Method. It is using it as part of the process.
If we remove the sensor creators and put all sensor creation inside the family factories, then we will have same code in simulation and edge factory. If we need to change something later we may have to change it in more then one place.
Also we lose the old /api/sensors creation flow and the separation we had in Phase 2.


6. Why add a `device_family` column on the existing `devices` table (with a default/backfill such as `"simulation"`) instead of a new table per family? What happens to Phase 2 sensor rows if you forget the backfill?
Ans:

A device is still a device weather it is simulation or edge. The existing devices table already have the common device information, so adding device_family is enough to tell which family it belongs to.
Making one table for simulation and another one for edge would basically duplicate the same structure and database logic. It also makes it harder when we want to query all devices together.
The new column is non-null, so the old Phase 2 rows also need a value.
That is why the old rows are given simulation during migration. If we forget the backfill or default then migration can fail because old rows don't have a value. And if they stay null, they can cause problem when we filter by family.


7. `POST /api/devices/provision` returns a kit (expected size: two sensors and two actuators). `GET /api/devices` can filter by `family` and `role`. Why must the UI be able to filter by family? Why do `/api/sensors` routes from Phase 2 still need to work?
Ans:

The family filter is needed so we can see only the devices from the family we selected.
For example if we select simulation, we dont want simulation and edge devices showing together because then it can be confusing which devices belong to which kit.
The role filter is also useful when we only want sensors or only actuators.
The old /api/sensors routes still need to work because Phase 3 is adding new functionality to Phase 2. It is not replacing the old sensor system.
So we still need to create and list individual sensors using the Factory Method from Phase 2.


## C. Compare, contrast, and scenarios

8. Draw the contrast in one paragraph: Factory Method vs Abstract Factory. Use the questions “which **one** product?” versus “which product **line**?” and mention that Abstract Factory often **uses** Factory Method–style methods inside.
Ans:

Factory Method is more like “which one product?”
For example in Phase 2 we ask for a moisture sensor or light sensor and the creator gives us that one sensor.
Abstract Factory is more like “which product line?”
In Phase 3 we choose simulation or edge and then we get the full set of related devices from that family.
Also Abstract Factory can use Factory Method inside it. That is basically what we are doing here because the family factory can use the Phase 2 sensor creators.
So they are not really replacing each other. They work together.


9. A DTO or HTTP handler constructs concrete simulation/edge device types directly, bypassing the family factory. What consistency bug can that reintroduce? How should HTTP stay on the abstract factory / service instead?
Ans:

If the HTTP handler creates the devices directly, then it can accidentally choose devices from different families.
For example it could create a simulation sensor and an edge actuator. It can also forget to set the correct family or protocol.
The HTTP part should only deal with request and response. It should get the family from the request and call something like DeviceFamilyService.provision_family(family).
Then the service chooses the correct family factory and factory creates the whole kit.
This way HTTP code dont need to know about concrete devices and the factory can make sure everything belongs to same family.
If the family is not supported, API can return 400 Bad Request.


10. Someone proposes a single “god factory” that creates locations, readings, and devices “because we already have a factory.” Why is that a misuse of Abstract Factory?
Ans:

Abstract Factory is for creating a family of related products. It is not suppose to create everything in the application just because we already have a factory.
Locations, readings and devices are different things. They have different rules and responsibilities.
If we put everything into one big factory, it will become too complicated and changes in one part can effect the other parts also.
So the device family factory should only deal with devices that belongs to same family, like sensors and actuators.
Other things like locations should have their own creation logic when needed.