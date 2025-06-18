# server.py
import subprocess
import os
from pathlib import Path
from typing import Dict, Any, Optional
from mcp.server.fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP("KnitScript Runner")


# Test tool
# @mcp.tool()
# def add(a: int, b: int) -> int:
#     """Add two numbers"""
#     return a + b


# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"


# Add file writing tool
@mcp.tool()
def write_file(file_path: str, content: str) -> Dict[str, Any]:
    """
    Write content to a file.
    
    Args:
        file_path: Path where the file should be saved
        content: Content to write to the file
    
    Returns:
        Dictionary containing success status and file path
    """
    try:
        path = Path(file_path)
        # Create parent directories if they don't exist
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the file
        path.write_text(content, encoding='utf-8')
        
        return {
            "success": True,
            "file_path": str(path.absolute()),
            "message": f"File successfully written to {path.absolute()}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to write file: {str(e)}",
            "file_path": None
        }


# Add KnitScript compilation tool
@mcp.tool()
def compile_knitscript(ks_file_path: str, k_output_path: Optional[str] = None, dat_output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Compile a KnitScript (.ks) file to Knitout (.k) and optionally DAT format.
    
    Args:
        ks_file_path: Path to the .ks KnitScript source file
        k_output_path: Optional path for .k output (defaults to same name as input)
        dat_output_path: Optional path for .dat output (if None, no DAT file is generated)
    
    Returns:
        Dictionary containing execution status and output paths
    """
    try:
        # Import KnitScript functions
        from knit_script.interpret_knit_script import knit_script_to_knitout_to_dat, knit_script_to_knitout
        
        # Validate input file exists
        input_path = Path(ks_file_path)
        if not input_path.exists():
            return {
                "success": False,
                "error": f"Input file not found: {ks_file_path}",
                "k_output_path": None,
                "dat_output_path": None
            }
        
        # Ensure it's a .ks file
        if input_path.suffix != '.ks':
            return {
                "success": False,
                "error": f"Input file must be a .ks KnitScript file, got: {input_path.suffix}",
                "k_output_path": None,
                "dat_output_path": None
            }
        
        # Generate output paths if not provided
        if k_output_path is None:
            k_output_path = str(input_path.with_suffix('.k'))
        
        # Empty placeholder for additional arguments
        additional_args = {}
        
        # Compile to Knitout
        if dat_output_path is not None:
            # If DAT output is explicitly requested, use the function that generates both
            knit_graph, machine_state = knit_script_to_knitout_to_dat(
                str(input_path), 
                k_output_path, 
                dat_output_path,
                pattern_is_filename=True, 
                python_variables=additional_args
            )
        else:
            # Just compile to Knitout
            knit_graph, machine_state = knit_script_to_knitout(
                str(input_path), 
                k_output_path, 
                pattern_is_filename=True, 
                python_variables=additional_args
            )
        
        # Create copies in the MCP's parent tmp folder
        mcp_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        #tmp_dir = mcp_dir.parent / "tmp"
        tmp_dir = mcp_dir / "tmp"
        tmp_dir.mkdir(exist_ok=True)
        
        # Copy files to tmp directory with same names
        copied_files = {}
        
        # Copy .k file
        if Path(k_output_path).exists():
            k_filename = Path(k_output_path).name
            k_tmp_path = tmp_dir / k_filename
            import shutil
            shutil.copy2(k_output_path, k_tmp_path)
            copied_files["k_tmp_path"] = str(k_tmp_path)
        
        # Copy .dat file if it exists
        if dat_output_path and Path(dat_output_path).exists():
            dat_filename = Path(dat_output_path).name
            dat_tmp_path = tmp_dir / dat_filename
            shutil.copy2(dat_output_path, dat_tmp_path)
            copied_files["dat_tmp_path"] = str(dat_tmp_path)
        
        result = {
            "success": True,
            "k_output_path": k_output_path,
            "ks_file_path": str(input_path),
            "message": "KnitScript compilation successful",
            **copied_files
        }
        
        if dat_output_path and Path(dat_output_path).exists():
            result["dat_output_path"] = dat_output_path
            
        return result
            
    except ImportError as e:
        return {
            "success": False,
            "error": f"KnitScript module not found. Make sure knit-script is installed: {str(e)}",
            "k_output_path": None,
            "dat_output_path": None
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"KnitScript compilation error: {str(e)}",
            "k_output_path": None,
            "dat_output_path": None
        }


# Update the convert_knitout_to_dat function to look in parent directory
@mcp.tool()
def convert_knitout_to_dat(file_path: str, output_format: Optional[str] = "dat") -> Dict[str, Any]:
    """
    Convert a Knitout (.k) file to DAT format using knitout-to-dat.js.
    Also saves a copy to the MCP parent's tmp folder for easy access.
    
    Args:
        file_path: Path to the .k Knitout file
        output_format: Output format (default: "dat")
    
    Returns:
        Dictionary containing execution status, output file path, and any messages
    """
    try:
        # Validate input file exists
        input_path = Path(file_path)
        if not input_path.exists():
            return {
                "success": False,
                "error": f"Input file not found: {file_path}",
                "output_path": None
            }
        
        # Ensure it's a .k file
        if input_path.suffix != '.k':
            return {
                "success": False,
                "error": f"Input file must be a .k Knitout file, got: {input_path.suffix}",
                "output_path": None
            }
        
        # Generate output file path
        output_path = input_path.with_suffix(f'.{output_format}')
        
        # Look for knitout-to-dat.js in parent directory
        script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        knitout_script = script_dir.parent / "knitout-to-dat.js"
        
        if not knitout_script.exists():
            # Fallback to current directory
            knitout_script = script_dir / "knitout-to-dat.js"
        
        # Prepare the command
        node_command = [
            "node", 
            str(knitout_script), 
            str(input_path), 
            str(output_path)
        ]
        
        # Execute the command
        node_process = subprocess.run(
            node_command, 
            capture_output=True, 
            text=True
        )
        
        # Check if execution was successful
        if node_process.returncode == 0:
            # Copy to tmp directory
            #tmp_dir = script_dir.parent / "tmp"
            tmp_dir = script_dir / "tmp"
            tmp_dir.mkdir(exist_ok=True)
            
            dat_filename = Path(output_path).name
            dat_tmp_path = tmp_dir / dat_filename
            
            import shutil
            shutil.copy2(output_path, dat_tmp_path)
            
            return {
                "success": True,
                "output_path": str(output_path),
                "dat_tmp_path": str(dat_tmp_path),
                "stdout": node_process.stdout,
                "stderr": node_process.stderr if node_process.stderr else None
            }
        else:
            return {
                "success": False,
                "error": f"Execution failed with return code {node_process.returncode}",
                "stdout": node_process.stdout,
                "stderr": node_process.stderr,
                "output_path": None
            }
            
    except FileNotFoundError:
        return {
            "success": False,
            "error": "Node.js or knitout-to-dat.js not found. Make sure Node.js is installed and knitout-to-dat.js is in the correct location.",
            "output_path": None
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "output_path": None
        }


@mcp.tool()
def check_knitscript_environment() -> Dict[str, Any]:
    """
    Check if the knitscript execution environment is properly set up.
    
    Returns:
        Dictionary with environment status information
    """
    results = {
        "node_available": False,
        "node_version": None,
        "knitout_script_exists": False,
        "knitout_script_path": "knitout-to-dat.js",
        "knitscript_available": False,
        "knitscript_module_available": False,
        "knitscript_version": None
    }
    
    try:
        # Check Node.js availability
        node_check = subprocess.run(
            ["node", "--version"], 
            capture_output=True, 
            text=True
        )
        if node_check.returncode == 0:
            results["node_available"] = True
            results["node_version"] = node_check.stdout.strip()
        
        # Check if knitout-to-dat.js exists in parent directory first
        script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        script_path = script_dir.parent / "knitout-to-dat.js"
        
        if not script_path.exists():
            # Fallback to current directory
            script_path = script_dir / "knitout-to-dat.js"
        
        if script_path.exists():
            results["knitout_script_exists"] = True
            results["knitout_script_path"] = str(script_path.absolute())
        
        # Check KnitScript Python module availability
        try:
            from knit_script.interpret_knit_script import knit_script_to_knitout
            results["knitscript_module_available"] = True
            
            # Try to get version if available
            import knit_script
            if hasattr(knit_script, '__version__'):
                results["knitscript_version"] = knit_script.__version__
        except ImportError:
            pass
        
        # Check KnitScript command line availability
        knit_script_cmd = "knit-script" if os.name != 'nt' else "knit_script.bat"
        ks_check = subprocess.run(
            [knit_script_cmd, "--version"], 
            capture_output=True, 
            text=True
        )
        if ks_check.returncode == 0:
            results["knitscript_available"] = True
            if not results["knitscript_version"]:
                results["knitscript_version"] = ks_check.stdout.strip()
        
    except Exception as e:
        results["error"] = str(e)
    
    return results


# Add a convenience tool to save and compile KnitScript in one step
# Update save_and_compile_knitscript to fix the DAT generation and add output info
@mcp.tool()
def save_and_compile_knitscript(file_path: str, content: str, generate_dat: bool = True) -> Dict[str, Any]:
    """
    Save KnitScript content to a file and compile it to Knitout (and optionally DAT).
    Also saves copies to the MCP parent's tmp folder for easy access.
    
    Args:
        file_path: Path where the .ks file should be saved
        content: KnitScript code content
        generate_dat: Whether to generate a DAT file (default: True)
    
    Returns:
        Dictionary containing success status and output paths
    """
    # First, save the file
    save_result = write_file(file_path, content)
    if not save_result["success"]:
        return save_result
    
    # Also save a copy to the tmp directory
    try:
        mcp_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        #tmp_dir = mcp_dir.parent / "tmp"
        tmp_dir = mcp_dir / "tmp"
        tmp_dir.mkdir(exist_ok=True)
        
        # Copy the .ks file to tmp
        ks_filename = Path(file_path).name
        ks_tmp_path = tmp_dir / ks_filename
        ks_tmp_path.write_text(content, encoding='utf-8')
        
        save_result["ks_tmp_path"] = str(ks_tmp_path)
    except Exception as e:
        # Non-fatal error, continue with compilation
        save_result["tmp_copy_error"] = str(e)
    
    # Then compile it
    # Fix: Generate DAT path when requested
    dat_path = str(Path(file_path).with_suffix('.dat')) if generate_dat else None
    compile_result = compile_knitscript(file_path, dat_output_path=dat_path)
    
    # If KnitScript compilation succeeded and generated .k file, try to convert to DAT using Node
    if compile_result["success"] and generate_dat and compile_result.get("k_output_path"):
        # Check if DAT was already generated by KnitScript
        if not compile_result.get("dat_output_path") or not Path(compile_result.get("dat_output_path", "")).exists():
            # Try using the Node.js converter as fallback
            dat_result = convert_knitout_to_dat(compile_result["k_output_path"])
            if dat_result["success"]:
                compile_result["dat_output_path"] = dat_result["output_path"]
                compile_result["dat_tmp_path"] = dat_result.get("dat_tmp_path")
                compile_result["node_dat_stdout"] = dat_result.get("stdout")
                compile_result["node_dat_stderr"] = dat_result.get("stderr")
    
    # Combine results
    return {
        "success": compile_result["success"],
        "ks_file_path": save_result["file_path"],
        "k_output_path": compile_result.get("k_output_path"),
        "dat_output_path": compile_result.get("dat_output_path"),
        "ks_tmp_path": save_result.get("ks_tmp_path"),
        "k_tmp_path": compile_result.get("k_tmp_path"),
        "dat_tmp_path": compile_result.get("dat_tmp_path"),
        "error": compile_result.get("error"),
        "knitscript_stdout": compile_result.get("stdout"),
        "knitscript_stderr": compile_result.get("stderr"),
        "node_dat_stdout": compile_result.get("node_dat_stdout"),
        "node_dat_stderr": compile_result.get("node_dat_stderr")
    }