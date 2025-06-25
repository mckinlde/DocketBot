# main.py

# main.py creates the driver, accepts a UBI number as input, and imports and calls
# various utility functions to implement the FavoriteButton spec.

# main.py does not do any of its own webscraping or pdf writing, and currently only
# performs calls for LNI, from which it gets scraped/parsed data to output to the console.

# FavouriteButton Spec:
# # FavoriteButton is a python program for New Matter Intake in Sarah King's Construction Dispute Practice
# # The main output is a filled 'assets\0000 New Matter Form.pdf'
# # The main input is a Washington State UBI number
# The Chrome and ChromeDriver Binaries used by Selenium are parameterized for easy reconfig, and on this machine located at:
        # self.chrome_binary = resource_path(os.path.join("chrome-win64", "chrome.exe"))
        # self.driver_binary = resource_path(os.path.join("chromedriver-win64", "chromedriver.exe"))
# # FavoriteButton uses selenium to navigate to the UBI-specific URLs for:
# Secretary of State (SOS): https://ccfs.sos.wa.gov/#/BusinessSearch/UBI/{UBI}
# LNI Verify a Contractor: https://secure.lni.wa.gov/verify/Detail.aspx?UBI={UBI}
# Department of Revenue: https://secure.dor.wa.gov/gteunauth/_/#1 (requires form submission, see DOR_form)

# If FavoriteButton can get directly to the UBI page, it does, otherwise it
# waits for the user to fill any necessary captchas and navigate to the page 
# for the business in question before pressing ENTER to continue

# From each page, it saves information, and then calls fill_pdf.py to write it to the PDF form.
