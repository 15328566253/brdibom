/*
 * The EXE writes a temporary .scr file that loads exportJson.il and calls
 * exportJson directly. This file is kept as a readable manual entry point
 * for users who prefer to run the bridge from the Allegro command window.
 */

procedure( ibomBridgeExport( exportJsonPath configPath rev company )
    load( exportJsonPath )
    exportJson(
        ?rev rev
        ?company company
        ?config configPath
    )
)

