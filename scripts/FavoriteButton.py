# # FavoriteButton.py is a python script for New Matter Intake in Sarah King's Construction Dispute Practice

# # The main output is a filled 'assets\0000 New Matter Form.pdf'
# # The main input is a Washington State UBI number
# The Chrome and ChromeDriver Binaries used by Selenium are parameterized for easy reconfig, and on this machine located at:

        # self.chrome_binary = resource_path(os.path.join("chrome-win64", "chrome.exe"))
        # self.driver_binary = resource_path(os.path.join("chromedriver-win64", "chromedriver.exe"))

# # FavoriteButton.py uses selenium to navigate to the UBI-specific URLs for:
# Secretary of State (SOS): https://ccfs.sos.wa.gov/#/BusinessSearch/UBI/{UBI}
# LNI Verify a Contractor: https://secure.lni.wa.gov/verify/Detail.aspx?UBI={UBI}
# Department of Revenue: https://secure.dor.wa.gov/gteunauth/_/#1 (requires form submission, see DOR_form)

# # DOR_Form:
# 1) Click the "business lookup button": (<span id="Dg-1-1_c" class="ColIconText">Business Lookup</span>)
# 2) Fill the UBI/Accound ID# field: (<div id="fc_Dc-s" data-name="Dc-s" class="FGFC FGCPTop FGCPTopVisible CTEC FGTBC FGControlText FieldEnabled Field FGFill"><span class="FGDW FGDWStandard"><label id="lb_Dc-s" class="FGD2 CTEW FGD2Standard" for="Dc-s"><a id="cl_Dc-s" href="#RLZy8PtWWnMkBnfP_Dc-s" class="CaptionLink DFL FastEvt" data-event="ShowTip" data-showtip="{&quot;lng&quot;:&quot;ENG&quot;,&quot;typ&quot;:&quot;WA.XDBLS&quot;,&quot;hsh&quot;:&quot;&quot;,&quot;idx&quot;:&quot;1&quot;,&quot;fmt&quot;:&quot;TEXT&quot;,&quot;key&quot;:&quot;HelpUBI&quot;}" tabindex="0"><span id="caption2_Dc-s" class="CTE CaptionLinkText  IconCaption ICPLeft IconCaptionSmall" style=""><span class="FICW FICWSmall CaptionIconWrapper"><span role="presentation" aria-hidden="true" class="FIC FICSmall CaptionIcon FICF FICF_Material FICFTAuto" data-iconfont="Material" data-icon="" data-iconstatus="Auto"><img class="FICImg FICImgSmall CaptionIcon" src="../Resource/Images/blank.gif" alt=""></span></span><span class="IconCaptionText">UBI/Account ID #</span></span></a><span id="indicator_Dc-s" class="FI FI"></span></label></span><div class="FGIW FGIWText FGIWFill"><div id="ic_Dc-s" class="FGIC" style=""><input type="text" autocomplete="off" name="Dc-s" id="Dc-s" class="DFI FieldEnabled Field CTEF DocControlText FastEvtFieldKeyDown FastFieldEnterEvent TAAuto TAAutoLeft FastEvtFieldFocus" value="" spellcheck="true" data-fast-enter-event="Dc-s" maxlength="250" tabindex="0" style=""></div></div></div>)
# 3) Prompt the user to complete the captcha, search, select the matching business, and return control to selenium by pressing Enter 

# If FavoriteButton.py can get directly to the UBI page, it does, otherwise it
# waits for the user to fill any necessary captchas and navigate to the page 
# for the business in question before pressing ENTER to continue

# From each page, it saves the following information:
#     From the secretary of state's corporate lookup:
#     - company name
#     - company addresses, mailing, and street
#     - if the company is currently active, and if not, the date of their inactivity
#     - Name of registered agent, and registered agent mailing and street address
#     - Governor names

#     from the LNI:
#     - Contractors registration number 
#     - bond company, amount, and bond number (sometimes there are more than one)
#     - Insurance company and amount
#     - if contractors license is suspended
#     - any active lawsuits against the bond, case number, county, parites, status 

#     Department of Revenue
#     - Entity name
#     - Business name
#     - Trade names, if any
#     - Governors

# Then, it uses that information to fill out the "assets\0000 New Matter Form.pdf", 
# merging multi-page overlays if > 9 parties by:
#     - Automatically splits parties across additional pages if there are more than 9
#     - Uses the first page as a template for all overlay pages
#     - Maintains clean formatting and spacing per page