# dor.py


# # DOR_Form:
# 1) Click the "business lookup button": (<span id="Dg-1-1_c" class="ColIconText">Business Lookup</span>)
# 2) Fill the UBI/Accound ID# field: (<div id="fc_Dc-s" data-name="Dc-s" class="FGFC FGCPTop FGCPTopVisible CTEC FGTBC FGControlText FieldEnabled Field FGFill"><span class="FGDW FGDWStandard"><label id="lb_Dc-s" class="FGD2 CTEW FGD2Standard" for="Dc-s"><a id="cl_Dc-s" href="#RLZy8PtWWnMkBnfP_Dc-s" class="CaptionLink DFL FastEvt" data-event="ShowTip" data-showtip="{&quot;lng&quot;:&quot;ENG&quot;,&quot;typ&quot;:&quot;WA.XDBLS&quot;,&quot;hsh&quot;:&quot;&quot;,&quot;idx&quot;:&quot;1&quot;,&quot;fmt&quot;:&quot;TEXT&quot;,&quot;key&quot;:&quot;HelpUBI&quot;}" tabindex="0"><span id="caption2_Dc-s" class="CTE CaptionLinkText  IconCaption ICPLeft IconCaptionSmall" style=""><span class="FICW FICWSmall CaptionIconWrapper"><span role="presentation" aria-hidden="true" class="FIC FICSmall CaptionIcon FICF FICF_Material FICFTAuto" data-iconfont="Material" data-icon="" data-iconstatus="Auto"><img class="FICImg FICImgSmall CaptionIcon" src="../Resource/Images/blank.gif" alt=""></span></span><span class="IconCaptionText">UBI/Account ID #</span></span></a><span id="indicator_Dc-s" class="FI FI"></span></label></span><div class="FGIW FGIWText FGIWFill"><div id="ic_Dc-s" class="FGIC" style=""><input type="text" autocomplete="off" name="Dc-s" id="Dc-s" class="DFI FieldEnabled Field CTEF DocControlText FastEvtFieldKeyDown FastFieldEnterEvent TAAuto TAAutoLeft FastEvtFieldFocus" value="" spellcheck="true" data-fast-enter-event="Dc-s" maxlength="250" tabindex="0" style=""></div></div></div>)
# 3) Prompt the user to complete the captcha, search, select the matching business, and return control to selenium by pressing Enter 

#     Department of Revenue
#     - Entity name
#     - Business name
#     - Trade names, if any
#     - Governors
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from utils import wait_for_continue


def get_dor_info(driver):
    try:
        driver.get("https://secure.dor.wa.gov/gteunauth/_/#1")
        print("DOR loaded. Complete CAPTCHA and select business, then ENTER.", end="")
        if not wait_for_continue():
            return {"status": "Not found"}

        # Placeholder return until scraper is implemented
        return {"status": "Not implemented"}

    except Exception as e:
        print(f"DOR error: {e}")
        return {"status": "error"}
