# model_sector.py

def build_sector_vba(R_out, Theta_deg,R_in,z):
    """
    生成扇形外圆弧的 VBA 字符串
    """

    sectorVba = f"""

StartVersionStringOverrideMode "2024.5|33.0.1|20240614" 
With Arc
     .Reset 
     .Name "Arc_Outer" 
     .Curve "curve1" 
     .Orientation "Clockwise" 
     .XCenter "0" 
     .YCenter "0" 
     .X1 "0" 
     .Y1 "{str(R_out)}" 
     .X2 "0.0" 
     .Y2 "0.0" 
     .Angle "{str(Theta_deg)}" 
     .UseAngle "True" 
     .Segments "0" 
     .Create
End With

StartVersionStringOverrideMode "2024.5|33.0.1|20240614" 
With Arc
     .Reset 
     .Name "Arc_Inner" 
     .Curve "curve1" 
     .Orientation "Clockwise" 
     .XCenter "0" 
     .YCenter "0" 
     .X1 "0" 
     .Y1 "{str(R_in)}" 
     .X2 "0.0" 
     .Y2 "0.0" 
     .Angle "{str(Theta_deg)}" 
     .UseAngle "True" 
     .Segments "0" 
     .Create
End With

StartVersionStringOverrideMode "2024.5|33.0.1|20240614" 
Pick.ClearAllPicks
'## Merged Block - store picked point: 1
StartVersionStringOverrideMode "2024.5|33.0.1|20240614" 
Pick.NextPickToDatabase "1" 
Pick.PickCurveEndpointFromId "curve1:Arc_Inner", "2"

'## Merged Block - store picked point: 2
StartVersionStringOverrideMode "2024.5|33.0.1|20240614" 
Pick.NextPickToDatabase "2" 
Pick.PickCurveEndpointFromId "curve1:Arc_Outer", "2"

'## Merged Block - define curve line: curve1:line1
StartVersionStringOverrideMode "2024.5|33.0.1|20240614" 
With Line
     .Reset 
     .Name "line1" 
     .Curve "curve1" 
     .X1 "xp(1)" 
     .Y1 "yp(1)" 
     .X2 "xp(2)" 
     .Y2 "yp(2)" 
     .Create
End With

'## Merged Block - store picked point: 3
StartVersionStringOverrideMode "2024.5|33.0.1|20240614" 
Pick.NextPickToDatabase "3" 
Pick.PickCurveEndpointFromId "curve1:Arc_Inner", "1"
'## Merged Block - store picked point: 4
StartVersionStringOverrideMode "2024.5|33.0.1|20240614" 
Pick.NextPickToDatabase "4" 
Pick.PickCurveEndpointFromId "curve1:Arc_Outer", "1"
'## Merged Block - define curve line: curve1:line2
StartVersionStringOverrideMode "2024.5|33.0.1|20240614" 
With Line
     .Reset 
     .Name "line2" 
     .Curve "curve1" 
     .X1 "xp(3)" 
     .Y1 "yp(3)" 
     .X2 "xp(4)" 
     .Y2 "yp(4)" 
     .Create
End With

'## Merged Block - new component: component1
StartVersionStringOverrideMode "2024.5|33.0.1|20240614" 
Component.New "component1"
'## Merged Block - define extrudeprofile: component1:sector
StartVersionStringOverrideMode "2024.5|33.0.1|20240614" 
With ExtrudeCurve
     .Reset 
     .Name "sector" 
     .Component "component1" 
     .Material "PEC" 
     .Thickness "{str(z)}" 
     .Twistangle "0.0" 
     .Taperangle "0.0" 
     .DeleteProfile "True" 
     .Curve "curve1:Arc_Inner" 
     .Create
End With
"""
    return sectorVba
