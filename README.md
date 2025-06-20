Xpand Home Exercise Test
========================

Task
----

Write code that controls a robot in the fulfillment of incoming orders. Each order consists of multiple items
(identified by SKU).

Layout
------

The items are laid out in a grid-like structure of "slots". Each slot can contain one or more items. Slots are divided
into "hives", each hive contains a subset of the slots. The following diagram illustrates this:

    ┌────────┬────────┐  ┌────────┬────────┐  ┌────────┬────────┐
    │        │        │  │        │        │  │        │        │
    ├────────┼────────┤  ├────────┼────────┤  ├────────┼────────┤
    │        │        │  │        │        │  │        │        │
    ├────────┼────────┤  ├────────┼────────┤  ├────────┼────────┤
    │        │        │  │        │        │  │        │        │
    ├────────┼────────┤  ├────────┼────────┤  ├────────┼────────┤
    │ A0.2.0 │ A0.2.1 │  │        │        │  │        │        │
    ├────────┼────────┤  ├────────┼────────┤  ├────────┼────────┤
    │ A0.1.0 │ A0.1.1 │  │        │        │  │        │        │
    ├────────┼────────┤  ├────────┼────────┤  ├────────┼────────┤
    │ A0.0.0 │ A0.0.1 │  │        │        │  │        │        │
    └────────┴────────┘  └────────┴────────┘  └────────┴────────┘ ...
            A0                   A1                   A2


Each hive is labelled alphanumerically, with each slot labelled starting with the hive prefix followed by row and column
(So in the example above all slots in the A0 hive start with "A0."). Each slot also has specific real-world coordinates
in mm (X,Y) that can be queried from the inventory DB.

Robot
-----

The robotic arm is placed on a moving base capable of moving in the X and Y axes. The robotic arm is able to perform
predefined motions such as PICK, FOLD, PLACE BAG, etc. Each motion takes a certain amount of time. To reflect this the
provided APIs use appropriate constructs for the relevant language, e.g async/await, Future, etc.

Requirements
------------

Interface definitions are provided with this test in several languages. Also contained in the sources for each language
is an empty class named OrderFulfiller. It has a single public method that receives an order to be fulfilled by the
robot. This class must be implemented to complete the test.

The interfaces expose two key entities:

 * Robot
 * Inventory DB

To accomplish its task, the OrderFulfiller should:

1. Query the inventory DB to find where the items are (in which slots) based on their SKUs.
2. Navigate the robot to the slots where the items are placed.
3. For each such slot execute the PICK robotic arm motion.
4. Notify the inventory DB that the item has been picked from the slot.
5. If PICK operation failed (false return value), notify the inventory DB that the slot is erroneous, and search for an
   alternative slot for this item.
6. If an item cannot be fulfilled, ignore and fulfil the items that can be fulfilled.
7. When all possible items are picked, navigate to slot A0.3.0 and execute the PLACE BAG robotic arm motion.
8. The region between X coordinates 1000 and 2000 is considered dangerous, and if the robot needs to pass through this
   region (in either direction), it must be placed in the FOLD position prior to entering the region. This means it has
   successfully finished executing the FOLD robotic arm motion. However, note that the robot can start the arm motion
   while starting movement along the X axis concurrently, as long as it is verified that the motion has finished before
   entering the danger region.
9. (Optional) When considering which slots to pick the items from, it would be beneficial for the fulfiller to pick only
   from one side of the danger region, if possible. If not, the next best thing would be to minimize movements through
   the danger region.

General Guidelines
------------------

 * Choice of language, framework etc. – is completely free. The provided interfaces are for illustration only, they can
   be translated to any desired language.
 * Code should be written with clean coding principles in mind – consider the separation to classes, methods, etc. Pay
   attention to reasonable code styling and formatting.
 * There is no need to spend more than two hours on the task – if the task is not finished within two hours, submit a
   partial solution.
 * Usage of AI-based IDEs and agent mode is allowed - but in this case the expected result should be a more complete
   solution with tests. The code that the AI produces must be reviewed and the AI guided to achieve the desired coding
   standards and solution architecture.
