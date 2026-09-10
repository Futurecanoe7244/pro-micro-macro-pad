# pro-micro-macro-pad
the 3d printable parts are not mine but you can download them from their respectful owner
here https://www.printables.com/model/109226-4x4-arduino-pro-micro-macropad


                    
                  
                  prerequisites
            you need python 3.x.x on installed on your computer
            you must run the pre-reqs.bat file to install the required
            python modules
                  
the build guide is in the root of the zip


  the hardware list
  
  1. arduino pro micro must be a pro micro
  2. 16 keyboard switches of desired type
  3. 3d printed parts
  4. wire preferrably two colors but one will work if you have a way to mark some of them
  5. solder better if lead but any kind for electronics will work
  6. keycaps custom ones you can make here easily to print https://vostoklabs.github.io/SVG-keycap-generator/
     for more icons visit here https://simpleicons.org/ must be printed with a 0.2mm nozzle
     and a printer that can do at least two colors
  7. hot glue and hot glue gun
  8. super glue
  9. kapton tape to insulate the arduino if printed insulator does not fit because of the wires being too long
  10. usb c cable for arduino than can transfer data
  11. machine screws and nuts the smallest screw with a matching nut is needed to put back plate on



all the code is included in the zip the code for the arduino is in the macro-control folder
and the code for the pc is in the host-code folder

if you want to have the python app start on boot just do windows+r and type shell:startup and place the vbs script
in the folder that just opened and use that script to open the app if you closed it it will go to your tray when 
it opens and it will also go to the tray if you minimize or x out of it to completely close it open your tray and 
there will be a blue dot that is the app

here is the circuit diagram 
before soldering push the keyboard switches through the front of the frame 

    -------------------------------------------------------------------------------
    2. SCHEMATIC WIRING DIAGRAM (VECTOR BLUEPRINT)
    -------------------------------------------------------------------------------
    This macro pad utilizes a standard diode-free matrix. Columns are pulsed as outputs, 
    while rows utilize internal pull-up resistors to detect drops to a ground state.

               [Col 1: Pin 9]  [Col 2: Pin 10] [Col 3: Pin 16] [Col 4: Pin 14]

                     |               |               |               |
    [Row 1: Pin 5] --+---[SW 1]-------+---[SW 2]-------+---[SW 3]-------+---[SW 4]

                     |               |               |               |
    [Row 2: Pin 6] --+---[SW 5]-------+---[SW 6]-------+---[SW 7]-------+---[SW 8]

                     |               |               |               |
    [Row 3: Pin 7] --+---[SW 9]-------+---[SW 10]------+---[SW 11]------+---[SW 12]

                     |               |               |               |
    [Row 4: Pin 8] --+---[SW 13]------+---[SW 14]------+---[SW 15]------+---[SW 16]


    * Wiring Mechanics:
      - Each [SW] represents a mechanical switch containing 2 contact pins.
      - Horizontal Row Pins: Connect one pin of all 4 switches in a row together.
      - Vertical Column Pins: Connect the remaining pin of all 4 switches in a column together.
      - No external resistors or physical blocking diodes are needed.

to program the arduino you need to install the arduino ide on your computer and set the com port to the one that your 
arduino is on and it should say arduino leonardo open the arduino code file included in the macro-control folder upload it to your arduino

once finished soldering and programming your arduino use hot glue and glue it down to the baseplate but make sure it is able to be plugged fully in once the baseplate then take your kapton tape and put it over the arduino to cover it but leave the pins where the wire are soldered on to are not covered

to finish it off take your smallest machine screw and put a matching nut on it and then screw it in the hole on the frame of the macro pad with the back on 
