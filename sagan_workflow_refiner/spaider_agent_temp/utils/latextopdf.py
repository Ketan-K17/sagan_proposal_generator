# # Make a proposal on advanced rocket engines


############################
############################
##### OLD SOLUTION #####
############################
############################


        
# import subprocess
# import os
# import platform
# import sys
# import shutil
# import logging
# from pathlib import Path
# from colorama import Fore, Style

# class LaTeXPipeline:
#     def __init__(self):
#         """Initialize the LaTeX pipeline with proper logging setup."""
#         # Setup logging first
#         self._setup_logging()
        
#         # Initialize other attributes
#         self.os_type = platform.system().lower()
#         self.latex_installed = False
#         self.package_manager = self._detect_package_manager()
        
#     def _setup_logging(self):
#         """Set up logging configuration."""
#         # Create logs directory if it doesn't exist
#         log_dir = Path('logs')
#         log_dir.mkdir(exist_ok=True)
        
#         # Configure logging
#         self.logger = logging.getLogger('latex_pipeline')
#         self.logger.setLevel(logging.INFO)
        
#         # Prevent duplicate handlers
#         if not self.logger.handlers:
#             # Console handler
#             console_handler = logging.StreamHandler()
#             console_handler.setLevel(logging.INFO)
#             console_formatter = logging.Formatter('%(levelname)s - %(message)s')
#             console_handler.setFormatter(console_formatter)
#             self.logger.addHandler(console_handler)
            
#             # File handler
#             file_handler = logging.FileHandler(log_dir / 'latex_pipeline.log')
#             file_handler.setLevel(logging.DEBUG)
#             file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#             file_handler.setFormatter(file_formatter)
#             self.logger.addHandler(file_handler)

#     def _detect_package_manager(self):
#         """Detect the system's package manager."""
#         if self.os_type == "linux":
#             package_managers = {
#                 "apt-get": "apt-get -v",
#                 "dnf": "dnf --version",
#                 "yum": "yum --version",
#                 "pacman": "pacman --version"
#             }
            
#             for pm, cmd in package_managers.items():
#                 try:
#                     result = subprocess.run(
#                         cmd.split(), 
#                         capture_output=True, 
#                         text=True, 
#                         timeout=30
#                     )
#                     if result.returncode == 0:
#                         self.logger.info(f"Detected package manager: {pm}")
#                         return pm
#                 except subprocess.TimeoutExpired:
#                     self.logger.warning(f"Command '{cmd}' timed out")
#                 except FileNotFoundError:
#                     continue
#                 except Exception as e:
#                     self.logger.warning(f"Error checking {pm}: {str(e)}")
        
#         self.logger.info("No supported package manager found")
#         return None

#     def _check_latex_installation(self):
#         """Check if LaTeX is installed."""
#         try:
#             # For macOS, check in the MacTeX location first
#             if self.os_type == "darwin":
#                 os.environ["PATH"] = f"/Library/TeX/texbin:{os.environ['PATH']}"
            
#             # Check pdflatex
#             pdflatex_result = subprocess.run(
#                 ["pdflatex", "--version"], 
#                 capture_output=True, 
#                 text=True,
#                 timeout=30
#             )
            
#             # Check latexmk
#             latexmk_result = subprocess.run(
#                 ["latexmk", "--version"], 
#                 capture_output=True, 
#                 text=True,
#                 timeout=30
#             )
            
#             # Log version information
#             if pdflatex_result.returncode == 0:
#                 self.logger.info(f"pdflatex version: {pdflatex_result.stdout.splitlines()[0]}")
#             if latexmk_result.returncode == 0:
#                 self.logger.info(f"latexmk version: {latexmk_result.stdout.splitlines()[0]}")
            
#             self.latex_installed = (
#                 pdflatex_result.returncode == 0 and 
#                 latexmk_result.returncode == 0
#             )
#             return self.latex_installed
            
#         except FileNotFoundError as e:
#             self.logger.error(f"LaTeX component not found: {str(e)}")
#             self.latex_installed = False
#             return False
#         except subprocess.TimeoutExpired:
#             self.logger.error("LaTeX version check timed out")
#             self.latex_installed = False
#             return False
#         except Exception as e:
#             self.logger.error(f"Unexpected error checking LaTeX: {str(e)}")
#             self.latex_installed = False
#             return False

#     def _install_latex_macos(self):
#         """Install MacTeX on macOS."""
#         self.logger.info("Attempting to install MacTeX on macOS...")
        
#         try:
#             # Check for Homebrew
#             brew_check = subprocess.run(
#                 ["brew", "--version"],
#                 capture_output=True,
#                 text=True
#             )
            
#             if brew_check.returncode != 0:
#                 self.logger.error("Homebrew is not installed")
#                 self.logger.info("Please install Homebrew by running:")
#                 self.logger.info('/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"')
#                 return False
            
#             # Update Homebrew
#             self.logger.info("Updating Homebrew...")
#             subprocess.run(
#                 ["brew", "update"],
#                 check=True,
#                 capture_output=True,
#                 text=True,
#                 timeout=300
#             )
            
#             # Install MacTeX
#             self.logger.info("Installing MacTeX (this may take a while)...")
#             result = subprocess.run(
#                 ["brew", "install", "mactex"],
#                 check=True,
#                 capture_output=True,
#                 text=True,
#                 timeout=1800  # 30 minutes timeout
#             )
            
#             # Update PATH to include MacTeX binaries
#             os.environ["PATH"] = f"/Library/TeX/texbin:{os.environ['PATH']}"
            
#             self.logger.info("MacTeX installation completed successfully")
#             return True
            
#         except subprocess.TimeoutExpired:
#             self.logger.error("Installation timed out")
#             return False
#         except subprocess.CalledProcessError as e:
#             self.logger.error(f"Installation failed: {e.stderr}")
#             return False
#         except Exception as e:
#             self.logger.error(f"Unexpected error during installation: {str(e)}")
#             return False

#     def _create_directories(self, output_dir):
#         """Create necessary directories for output files."""
#         try:
#             os.makedirs(output_dir, exist_ok=True)
#             self.logger.info(f"Created output directory: {output_dir}")
#             return True
#         except Exception as e:
#             self.logger.error(f"Failed to create directory {output_dir}: {str(e)}")
#             return False

#     def latex_to_pdf(self, tex_file_path, output_dir=None):
#         """
#         Convert LaTeX to PDF with robust error handling.
        
#         Args:
#             tex_file_path (str): Path to the .tex file
#             output_dir (str, optional): Output directory for the PDF
            
#         Returns:
#             dict: State dictionary containing success status and any error messages
#         """
#         state = {
#             "success": False,
#             "error_message": None,
#             "pdf_path": None
#         }
        
#         try:
#             # Convert paths to absolute paths
#             tex_file_path = os.path.abspath(tex_file_path)
#             if output_dir is None:
#                 output_dir = os.path.dirname(tex_file_path)
#             output_dir = os.path.abspath(output_dir)
            
#             # Ensure the .tex file exists
#             if not os.path.exists(tex_file_path):
#                 state["error_message"] = f"LaTeX file not found: {tex_file_path}"
#                 return state
            
#             # Create output directory
#             if not self._create_directories(output_dir):
#                 state["error_message"] = f"Failed to create output directory: {output_dir}"
#                 return state
            
#             # Compile the document
#             base_name = os.path.splitext(os.path.basename(tex_file_path))[0]
#             pdf_path = os.path.join(output_dir, f"{base_name}.pdf")
            
#             try:
#                 # First attempt with pdflatex
#                 self.logger.info("Attempting compilation with pdflatex...")
#                 subprocess.run(
#                     [
#                         "pdflatex",
#                         "-interaction=nonstopmode",
#                         f"-output-directory={output_dir}",
#                         tex_file_path
#                     ],
#                     check=True,
#                     capture_output=True,
#                     text=True,
#                     timeout=300
#                 )
                
#                 # Check if PDF was generated
#                 if os.path.exists(pdf_path):
#                     state["success"] = True
#                     state["pdf_path"] = pdf_path
#                     self.logger.info(f"PDF generated successfully: {pdf_path}")
#                     return state
                    
#             except subprocess.CalledProcessError as e:
#                 self.logger.warning(f"pdflatex compilation failed: {e.stderr}")
#             except Exception as e:
#                 self.logger.warning(f"Error during pdflatex compilation: {str(e)}")
            
#             # If pdflatex failed, try latexmk
#             try:
#                 self.logger.info("Attempting compilation with latexmk...")
#                 subprocess.run(
#                     [
#                         "latexmk",
#                         "-pdf",
#                         "-interaction=nonstopmode",
#                         f"-output-directory={output_dir}",
#                         tex_file_path
#                     ],
#                     check=True,
#                     capture_output=True,
#                     text=True,
#                     timeout=300
#                 )
                
#                 if os.path.exists(pdf_path):
#                     state["success"] = True
#                     state["pdf_path"] = pdf_path
#                     self.logger.info(f"PDF generated successfully: {pdf_path}")
#                     return state
                    
#             except subprocess.CalledProcessError as e:
#                 error_msg = f"LaTeX compilation failed: {e.stderr}"
#                 state["error_message"] = error_msg
#                 self.logger.error(error_msg)
#             except Exception as e:
#                 error_msg = f"Unexpected error during compilation: {str(e)}"
#                 state["error_message"] = error_msg
#                 self.logger.error(error_msg)
            
#         except Exception as e:
#             state["error_message"] = f"Process error: {str(e)}"
#             self.logger.error(f"Process failed: {str(e)}")
        
#         return state

#     def cleanup_auxiliary_files(self, tex_file_path, output_dir=None):
#         """Clean up auxiliary files generated during compilation."""
#         try:
#             if output_dir is None:
#                 output_dir = os.path.dirname(tex_file_path)
            
#             base_name = os.path.splitext(os.path.basename(tex_file_path))[0]
#             extensions = [
#                 '.aux', '.log', '.out', '.fls', '.fdb_latexmk', 
#                 '.synctex.gz', '.dvi', '.bbl', '.blg'
#             ]
            
#             for ext in extensions:
#                 aux_file = os.path.join(output_dir, base_name + ext)
#                 if os.path.exists(aux_file):
#                     try:
#                         os.remove(aux_file)
#                         self.logger.debug(f"Removed auxiliary file: {aux_file}")
#                     except PermissionError:
#                         self.logger.warning(f"Permission denied: Could not remove {aux_file}")
#                     except Exception as e:
#                         self.logger.warning(f"Could not remove {aux_file}: {str(e)}")
            
#             return True
            
#         except Exception as e:
#             self.logger.error(f"Error during cleanup: {str(e)}")
#             return False


############################
############################
##### JYOTI'S SOLUTION #####
############################
############################


import subprocess
import os
import platform
import sys
import shutil
import logging
from pathlib import Path
from colorama import Fore, Style

class LaTeXPipeline:
    def init(self):
        """Initialize the LaTeX pipeline with proper logging setup."""
        
        # Initialize other attributes
        self.os_type = platform.system().lower()
        self.latex_installed = False
        
        # Set package manager based on OS
        if self.os_type == "linux":
            self.package_manager = self._detect_package_manager()
        elif self.os_type == "darwin":
            self.package_manager = "homebrew"
        else:
            self.package_manager = "miktex"


    def _detect_package_manager(self):
        """Detect the system's package manager."""
        if self.os_type == "linux":
            package_managers = {
                "apt-get": "apt-get -v",
                "dnf": "dnf --version",
                "yum": "yum --version",
                "pacman": "pacman --version"
            }
            
            for pm, cmd in package_managers.items():
                
                result = subprocess.run(
                    cmd.split(), 
                    capture_output=True, 
                    text=True, 
                    timeout=30
                )
                if result.returncode == 0:
                    return pm
                
        elif self.os_type == "windows":
            # Check for MiKTeX installation
            try:
                miktex_path = r"C:\Program Files\MiKTeX\miktex\bin\x64\miktex.exe"
                if os.path.exists(miktex_path):
                    return "miktex"
                    
                # Check in user's AppData folder (user installation)
                user_miktex = os.path.expandvars(r"%LOCALAPPDATA%\Programs\MiKTeX\miktex\bin\x64\miktex.exe")
                if os.path.exists(user_miktex):
                    return "miktex"
                    
                # Check for Chocolatey as fallback
                result = subprocess.run(
                    ["choco", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    return "chocolatey"
                    
            except:
                print("Failed to detect package manager for Windows")
                
        elif self.os_type == "darwin":
            try:
                # Check for Homebrew
                result = subprocess.run(
                    ["brew", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    return "homebrew"
            except Exception as e:
                print(e)
                
        return None

    def _check_latex_installation(self):
        """Check if LaTeX is installed."""
        try:
            if self.os_type == "windows":
                # Check Windows-specific paths
                miktex_path = r"C:\Program Files\MiKTeX\miktex\bin\x64"
                if os.path.exists(miktex_path):
                    os.environ["PATH"] = f"{miktex_path};{os.environ['PATH']}"
            elif self.os_type == "darwin":
                # macOS path handling
                os.environ["PATH"] = f"/Library/TeX/texbin:{os.environ['PATH']}"
            
            # Check pdflatex
            pdflatex_result = subprocess.run(
                ["pdflatex", "--version"], 
                capture_output=True, 
                text=True,
                timeout=30
            )
            
            # Check latexmk
            latexmk_result = subprocess.run(
                ["latexmk", "--version"], 
                capture_output=True, 
                text=True,
                timeout=30
            )
            
        
            
            self.latex_installed = (
                pdflatex_result.returncode == 0 and 
                latexmk_result.returncode == 0
            )
            return self.latex_installed
            
        except FileNotFoundError as e:
            # self.logger.error(f"LaTeX component not found: {str(e)}")
            self.latex_installed = False
            return False
        except subprocess.TimeoutExpired:
            # self.logger.error("LaTeX version check timed out")
            self.latex_installed = False
            return False
        except Exception as e:
            # self.logger.error(f"Unexpected error checking LaTeX: {str(e)}")
            self.latex_installed = False
            return False
        
    def _install_latex_macos(self):
        """Install MacTeX on macOS."""
        
        try:
            # Check for Homebrew
            brew_check = subprocess.run(
                ["brew", "--version"],
                capture_output=True,
                text=True
            )
            
            if brew_check.returncode != 0:
                # self.logger.error("Homebrew is not installed")
                # self.logger.info("Please install Homebrew by running:")
                # self.logger.info('/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"')
                return False
            
            # Update Homebrew
            # self.logger.info("Updating Homebrew...")
            subprocess.run(
                ["brew", "update"],
                check=True,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # Install MacTeX
            # self.logger.info("Installing MacTeX (this may take a while)...")
            result = subprocess.run(
                ["brew", "install", "mactex"],
                check=True,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutes timeout
            )
            
            # Update PATH to include MacTeX binaries
            os.environ["PATH"] = f"/Library/TeX/texbin:{os.environ['PATH']}"
            
            # self.logger.info("MacTeX installation completed successfully")
            return True
            
        except subprocess.TimeoutExpired:
            # self.logger.error("Installation timed out")
            return False
        except subprocess.CalledProcessError as e:
            # self.logger.error(f"Installation failed: {e.stderr}")
            return False
        except Exception as e:
            # self.logger.error(f"Unexpected error during installation: {str(e)}")
            return False

    def _install_latex_windows(self):
        """Install MiKTeX on Windows."""
        
        try:
            # Download MiKTeX installer
            import urllib.request
            import tempfile
            
            miktex_url = "https://miktex.org/download/win/basic-miktex-x64.exe"
            installer_path = os.path.join(tempfile.gettempdir(), "basic-miktex-x64.exe")
            
            # self.logger.info("Downloading MiKTeX installer...")
            urllib.request.urlretrieve(miktex_url, installer_path)
            
            # Run installer silently
            result = subprocess.run(
                [installer_path, "--unattended", "--shared"],
                check=True,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutes timeout
            )
            
            # Add MiKTeX to PATH
            miktex_path = r"C:\Program Files\MiKTeX\miktex\bin\x64"
            if miktex_path not in os.environ["PATH"]:
                os.environ["PATH"] = f"{miktex_path};{os.environ['PATH']}"
            
            # Initialize MiKTeX
            subprocess.run(
                ["initexmf", "--admin", "--set-config-value=[MPM]AutoInstall=1"],
                check=True,
                shell=True
            )
            
            # Update package database
            subprocess.run(
                ["miktex", "--admin", "packages", "update"],
                check=True,
                shell=True
            )
            
        except:
            print("Error installing Latex for windows system")



    def latex_to_pdf(self, tex_file_path, output_dir=None):
        """
        Convert LaTeX to PDF with robust error handling.
        
        Args:
            tex_file_path (str): Path to the .tex file
            output_dir (str, optional): Output directory for the PDF
            
        Returns:
            dict: State dictionary containing success status and any error messages
        """
        state = {
            "success": False,
            "error_message": None,
            "pdf_path": None
        }
        
        try:
            # Convert paths to absolute paths
            tex_file_path = os.path.abspath(tex_file_path)
            if output_dir is None:
                output_dir = os.path.dirname(tex_file_path)
            output_dir = os.path.abspath(output_dir)
            
            # Ensure the .tex file exists
            if not os.path.exists(tex_file_path):
                state["error_message"] = f"LaTeX file not found: {tex_file_path}"
                return state
            
            # Create output directory
            if not self._create_directories(output_dir):
                state["error_message"] = f"Failed to create output directory: {output_dir}"
                return state
            
            # Compile the document
            base_name = os.path.splitext(os.path.basename(tex_file_path))[0]
            pdf_path = os.path.join(output_dir, f"{base_name}.pdf")
            
            try:
                # First attempt with pdflatex
                self.logger.info("Attempting compilation with pdflatex...")
                subprocess.run(
                    [
                        "pdflatex",
                        "-interaction=nonstopmode",
                        f"-output-directory={output_dir}",
                        tex_file_path
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                # Check if PDF was generated
                if os.path.exists(pdf_path):
                    state["success"] = True
                    state["pdf_path"] = pdf_path
                    self.logger.info(f"PDF generated successfully: {pdf_path}")
                    return state
                    
            except subprocess.CalledProcessError as e:
                self.logger.warning(f"pdflatex compilation failed: {e.stderr}")
            except Exception as e:
                self.logger.warning(f"Error during pdflatex compilation: {str(e)}")
            
            # If pdflatex failed, try latexmk
            try:
                self.logger.info("Attempting compilation with latexmk...")
                subprocess.run(
                    [
                        "latexmk",
                        "-pdf",
                        "-interaction=nonstopmode",
                        f"-output-directory={output_dir}",
                        tex_file_path
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if os.path.exists(pdf_path):
                    state["success"] = True
                    state["pdf_path"] = pdf_path
                    self.logger.info(f"PDF generated successfully: {pdf_path}")
                    return state
                    
            except subprocess.CalledProcessError as e:
                error_msg = f"LaTeX compilation failed: {e.stderr}"
                state["error_message"] = error_msg
                self.logger.error(error_msg)
            except Exception as e:
                error_msg = f"Unexpected error during compilation: {str(e)}"
                state["error_message"] = error_msg
                self.logger.error(error_msg)
            
        except Exception as e:
            state["error_message"] = f"Process error: {str(e)}"
            self.logger.error(f"Process failed: {str(e)}")
        
        return state

    def cleanup_auxiliary_files(self, tex_file_path, output_dir=None):
        """Clean up auxiliary files generated during compilation."""
        try:
            if output_dir is None:
                output_dir = os.path.dirname(tex_file_path)
            
            base_name = os.path.splitext(os.path.basename(tex_file_path))[0]
            extensions = [
                '.aux', '.log', '.out', '.fls', '.fdb_latexmk', 
                '.synctex.gz', '.dvi', '.bbl', '.blg'
            ]
            
            for ext in extensions:
                aux_file = os.path.join(output_dir, base_name + ext)
                if os.path.exists(aux_file):
                    try:
                        os.remove(aux_file)
                        self.logger.debug(f"Removed auxiliary file: {aux_file}")
                    except PermissionError:
                        self.logger.warning(f"Permission denied: Could not remove {aux_file}")
                    except Exception as e:
                        self.logger.warning(f"Could not remove {aux_file}: {str(e)}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
            return False
