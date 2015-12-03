#import "BlePeripheral.h"

@implementation BlePeripheral
-(id) init
{
    if((self = [super init])) {
        self.m_powerBladeID = 0;
        self.m_sequenceNum = 0;
        self.m_time = 0;
        self.m_vRMS = 0;
        self.m_tPower = 0;
        self.m_aPower = 0;
        self.m_wHr = 0;
        self.m_flags = @"";
        self.m_adr = @"";
        self.m_numConnections = 0;
        self.m_pfactor = 0;
        self.m_rssi = 0;
        self.last_time = @"";
    }
    return self;
}
@end
