# MCP Server for compiling knitscript files to knitout and knitout to dat.

## Initial setup (if packages not already installed)

Install uv (https://docs.astral.sh/uv/getting-started/installation/)

``uv add "mcp[cli]"``

Initialize the folder with the necessary files (if starting over or configuring for first time)

``uv init knitscript-mcp-runner``

Install any python packages using uv (knitscript required)

``uv pip install knit-script``

can check with: ``uv pip show -f knit-script``

## Updating/reloading after making changes

cd into mcp server directory (this repository)

``uv run mcp install main.py``

## Editing

All MCP code is located in the main.py file. You must close and re-open claude desktop for changes to take effect.

## dat compiler requirement

This requires a dat compiler that is not included. knitout-to-dat.js must be added to this directory, or you can use your own compiler and update the code accordingly. 