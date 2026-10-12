# Phase 4 — Builder questions

**Pattern / focus:** Builder.

**Read first:** [Guide 04](../../materials/guides/04-builder.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example flight itineraries) as if they were your greenhouse classes.
- When a question asks about *this application*, refer to locations, zones, `location_id`, and the configuration wizard from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.

## A. Pattern

1. State the intent of Builder in plain language. Why does construction of a complex object need **stepwise assembly** and **validation at the end** (`build()`), instead of a telescoping constructor or a half-filled dict written straight to the database?
Ans:

Builder is basically used when we have a complex object and we need to build it step by step instead of putting everything in one big constructor.
In this case a location config have a location name and multiple zones, and every zone can have different settings. If we use a big constructor with lots of optional values it can become confusing and easy to make mistake.
We can also just use a dict and put everything directly in database, but the dict can be missing something or have wrong values.
With Builder we first keep all the values while building the object and then build() checks everything at the end. If everything is correct then it gives the complete object. If not, it gives an error before anything is saved to database.


2. Name the main participants (**product**, **builder**, **optional director**, **client**). Until `build()` succeeds, is the intermediate object a finished domain product? Why does that distinction matter?
Ans:

The main parts are:
Product: LocationConfig which contains the Location and its zones.
Builder: LocationConfigBuilder which keeps the location name and zone values and then validates them in build().
Director: There is no separate Director class in this project. If we had one, it could control a standard order of builder steps.
Client: LocationConfigService uses the builder and then sends the finished config to the repository.
Before build() is successful, it is not a finished domain object yet. It can still be missing name or zones or can have wrong threshold values.
This is important because we should only save the finished valid object. Also once the product is build, the later changes in builder should not change that already created product.


3. List at least three kinds of invalid configuration a location/zone `build()` should reject in **this** lab (name, zones, moisture thresholds). Why must those rules live in the **domain** builder, not only in the HTTP layer?
Ans:

The builder should reject things like empty location name or only spaces, and also a location with no zones.
A zone should not have empty name either. It should also reject moisture values outside the 0.0 - 1.0 range.
The low moisture threshold should be smaller then the high threshold. Also duplicate zone names in same location should not be allowed.
These are not just HTTP rules. They are rules for what a valid greenhouse configuration actually is.
If we only validate in FastAPI or Pydantic, another part of the application can skip that validation. For example a background job or import script can send invalid data.
So keeping the rules in builder means every place which uses the builder gets the same validation.


## B. This phase of the application

4. What aggregate does the builder produce (location plus zones)? Why does this course use **`location_id`** (and never `greenhouse_id`) as the name for that scope?
Ans:

The builder creates a LocationConfig which basically contains one Location and one or more zone objects.
Each zone has a location_id which connects it to the location row in the database.
The project uses location and location_id as the name for this scope in the database and API.
So we should keep using location_id. Using greenhouse_id would just create another name for same thing and it would not match the required schema and API.


5. Describe the path from API request to persistence: DTO → builder steps → `build()` → repository. What must **not** be persisted if `build()` raises `ConfigurationError` (or equivalent)?
Ans:

First the API gets the request and parses it using BuildLocationConfigRequestDto.
Then it calls LocationConfigService.
The service creates a LocationConfigBuilder, gives it the location name using with_location_name(), and then adds each zone using add_zone().
After that it calls build().
If everything is valid, the builder returns the completed LocationConfig and then the service gives it to LocationRepository to save it.
If build() gives a ConfigurationError, repository should not be called.
So in that case no location or zone from that invalid request should be saved in database.


6. Saving a location and its zones must be **one transaction**. What goes wrong if the location row commits and a later zone insert fails? How does that relate to “no half-built aggregates in the database”?
Ans:

If the location is saved first and then one of the zone inserts fails, we can end up with a location in database without all its zones.
For example maybe the location row is created but only 1 out of 3 zones gets saved. Then we have a half built configuration in the database.
That is not what user asked for because the complete configuration was not created successfully.
So the repository should save the location, get its ID, save all the zones with that location_id, and only commit at the end.
If anything fails then everything should be rolled back.
So its basically all or nothing. Either the full location and zones are saved or nothing is saved.


7. The configuration wizard UI collects fields in steps. How does that UI map to Builder without turning React (or the HTTP handler) into the place that owns domain validation?
Ans:

The React wizard collects the values step by step.
User can enter location name, add zones and enter the threshold and schedule values.
React can do some simple checks like showing that a field is empty before submitting. That is useful for user, but those are not the main domain rules.
When user submits, the UI sends one request DTO.
Then the HTTP handler only parses the request and calls the service. The service takes the DTO values and sends them into the builder.
Finally LocationConfigBuilder.build() does the real validation.
So even if the request comes from somewhere else and not React, the same rules will still be used.


## C. Compare, contrast, and scenarios

8. Contrast Builder with Factory Method and with Abstract Factory. Which pattern answers “which type?”, which answers “which matching kit?”, and which answers “how do we assemble one **valid whole** in steps?”
Ans:

Factory Method answers “which type?”
For example in Phase 2 we use it to create one sensor type, like moisture sensor or light sensor.
Abstract Factory answers “which matching kit?”
In Phase 3 we choose simulation or edge and get a full group of sensors and actuators which belong to same family.
Builder answers “how do we assemble one valid whole in steps?”
In Phase 4 we collect the location name and zones step by step, then check everything together and create one complete location configuration.
So all 3 patterns are doing different things and they can be used together in same application.


9. Fluent method chaining (`builder.add_zone(...).build()`) is a coding style. Why is a fluent interface **not** the same thing as the Builder pattern?
Ans:

Fluent interface is basically just a style where methods return the same object so we can keep chaining them.
For example: builder.add_zone(...).build()
But just because we can chain methods does not mean it is Builder pattern.
Builder is about keeping the unfinished values separate while we are building the object and then using something like build() to validate everything and create the final object.
So chaining is just how we can use the builder easily. The actual important part is the step by step construction and final validation.


10. A classmate validates thresholds only in FastAPI / Pydantic and leaves `build()` empty. Another mutates builder fields after `build()` while treating the product as immutable. Explain why each is a trap.
Ans:

If we only validate the threshold values in FastAPI or Pydantic, then another caller can bypass it.
For example a background job or import tool may call the application in a different way and invalid configuration can get through.
So build() still need to check the domain rules. Pydantic validation is useful for the HTTP request, but it should not be the only validation.
The builder can have mutable values while we are building the object, thats normal. But after build() the product should be separate and should not change when we change the builder.
If the finished object uses the same mutable lists or dictionaries from the builder, then changing the builder later can also change the already created product without us expecting it.
In this project the finished location and zones are frozen and the zones are stored in a tuple. The schedule is also copied into read-only structures.
So after the object is build, later changes to the builder or input values should not change that product.