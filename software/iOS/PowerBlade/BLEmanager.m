
#import "BLEmanager.h"
#import "BlePeripheral.h"

@implementation BLEmanager
@synthesize m_manger;
@synthesize m_peripheral;
@synthesize m_array_peripheral;
@synthesize mange_delegate;

#undef	AS_SINGLETON
#define AS_SINGLETON( __class ) \
+ (__class *)sharedInstance;

#undef	DEF_SINGLETON
#define DEF_SINGLETON( __class ) \
+ (__class *)sharedInstance \
{ \
static dispatch_once_t once; \
static __class * __singleton__; \
dispatch_once( &once, ^{ __singleton__ = [[__class alloc] init]; } ); \
return __singleton__; \
}


NSMutableDictionary *last_seen;


static BLEmanager *sharedBLEmanger=nil;
-(id)init
{
    self = [super init];
    if (self) {
        if (!m_array_peripheral) {
            m_manger = [[CBCentralManager alloc]initWithDelegate:self queue:nil];
            m_array_peripheral = [[NSMutableArray alloc]init];
            last_seen = [NSMutableDictionary dictionary];
        }
    }
    return self;
}


+(BLEmanager *)shareInstance;
{
    @synchronized(self){
        if (sharedBLEmanger == nil) {
            sharedBLEmanger = [[self alloc]init];
        }
    }
    return sharedBLEmanger;
}

-(void)initCentralManger;
{
    m_manger = [[CBCentralManager alloc]initWithDelegate:self queue:nil];
}

- (void)centralManagerDidUpdateState:(CBCentralManager *)central;
{
    if (central.state == CBCentralManagerStatePoweredOff) {
        NSLog(@"Please turn on BLE!");
    }
}

-(void) cleanData {
    NSNumberFormatter *f = [[NSNumberFormatter alloc] init];
    f.numberStyle = NSNumberFormatterDecimalStyle;
    NSDateFormatter *timeFormatter = [[NSDateFormatter alloc] init];
    [timeFormatter setDateFormat:@"MM/dd/yyyy HH:mm:ss"];
    [timeFormatter setTimeZone:[NSTimeZone timeZoneWithName:@"GMT"]];
    NSString * newTime = [timeFormatter stringFromDate:[[NSDate alloc]init]];
    for (id key in last_seen) {
        NSLog(@"last_seen key: %@, value: %@ \n", key, [last_seen objectForKey:key]);
        NSLog(@"last_seen TIME %@", [last_seen objectForKey:key]);
        NSDate *date1= [timeFormatter dateFromString:[last_seen objectForKey:key]];
        NSDate *date2= [timeFormatter dateFromString:newTime];
        NSLog(@"last_seen time %@", date1);
        NSTimeInterval distanceBetweenDates = [date2 timeIntervalSinceDate:date1];
        NSLog(@"last_seen interval %@ %f", key, distanceBetweenDates);
        if (distanceBetweenDates >= 5){
            for (int i = 0; i < m_array_peripheral.count; i++) {
                BlePeripheral * cur = [m_array_peripheral objectAtIndex:i];
                if (cur != NULL) {
                    NSLog(@"ID: %ld", cur.m_powerBladeID);
                    NSString * key_srt = [NSString stringWithFormat:@"%@", key];
                    NSString * powerBladeId = [NSString stringWithFormat:@"%ld", cur.m_powerBladeID];
                    if ([key_srt isEqualToString:powerBladeId] ) {
                        [m_array_peripheral removeObjectAtIndex:i];
                    }
                }
            }
        }

    }
    

    
    
}

- (void)centralManager:(CBCentralManager *)central didDiscoverPeripheral:(CBPeripheral *)peripheral advertisementData:(NSDictionary *)advertisementData RSSI:(NSNumber *)RSSI;
{
    [self cleanData];
    
    NSDateFormatter *timeFormatter = [[NSDateFormatter alloc] init];
    [timeFormatter setDateFormat:@"MM/dd/yyyy HH:mm:ss"];
    [timeFormatter setTimeZone:[NSTimeZone timeZoneWithName:@"GMT"]];
    NSString * newTime = [timeFormatter stringFromDate:[[NSDate alloc]init]];
    
    NSArray *keys = [advertisementData allKeys];
    for (int i = 0; i < [keys count]; ++i) {
        id key = [keys objectAtIndex: i];
        NSString *keyName = (NSString *) key;
        NSObject *value = [advertisementData objectForKey: key];
        if ([keyName isEqualToString:@"kCBAdvDataManufacturerData"]) {
            const char *valueString = [[value description] cStringUsingEncoding: NSUTF8StringEncoding];
            BlePeripheral *l_per = [self parseValueString:[NSString stringWithUTF8String:valueString] :peripheral RSSI:RSSI];
            l_per.m_peripheral = peripheral;
            BOOL isExist = [self isPeripheralEqual:peripheral RSSI:RSSI];
            if (!isExist && l_per != NULL) {
                l_per.last_time = newTime;
                [m_array_peripheral addObject:l_per];
                [last_seen setObject:newTime forKey:[NSNumber numberWithInt:l_per.m_powerBladeID]];
            }
            if (isExist && l_per != NULL) {
                if ([m_array_peripheral count]>0) {
                    for (int i=0;i<[m_array_peripheral count];i++) {
                        BlePeripheral *tmp_per = [m_array_peripheral objectAtIndex:i];
                        if (l_per.m_powerBladeID  == tmp_per.m_powerBladeID) {
                            NSLog(@"HIT!");
                            [last_seen setObject:newTime forKey:[NSNumber numberWithInt:l_per.m_powerBladeID]];
                            l_per.m_rssi = [RSSI doubleValue];
                            BlePeripheral *r_per = [self parseValueString:[NSString stringWithUTF8String:valueString] :peripheral RSSI:RSSI];
                            l_per.m_aPower = r_per.m_aPower;
                            l_per.m_flags = r_per.m_flags;
                            l_per.m_numConnections = r_per.m_numConnections;
                            l_per.m_pfactor = r_per.m_pfactor;
                            l_per.m_sequenceNum = r_per.m_sequenceNum;
                            l_per.m_time = r_per.m_time;
                            l_per.m_tPower = r_per.m_tPower;
                            l_per.m_vRMS = r_per.m_vRMS;
                            l_per.m_wHr = r_per.m_wHr;
                            l_per.last_time = newTime;
                            [m_array_peripheral replaceObjectAtIndex:i withObject:l_per];
                        }
                    }
                }
            }
        }
        
    }

}

-(NSString *) fixMsg:(NSString *) msg {
    NSArray* words = [msg componentsSeparatedByCharactersInSet :[NSCharacterSet whitespaceAndNewlineCharacterSet]];
    msg = [words componentsJoinedByString:@""];
    msg = [msg stringByReplacingOccurrencesOfString:@"<" withString:@""];
    msg = [msg stringByReplacingOccurrencesOfString:@">" withString:@""];
    return msg;
}

- (NSNumber *)convertBinaryStringToDecimalNumber:(NSString *)binaryString {
    NSUInteger totalValue = 0;
    for (int i = 0; i < binaryString.length; i++) {
        totalValue += (int)([binaryString characterAtIndex:(binaryString.length - 1 - i)] - 48) * pow(2, i);
    }
    return @(totalValue);
}

- (NSNumber *)convertBase10BinaryStringToDecimalNumber:(NSString *)binaryString {
    NSUInteger totalValue = 0;
    for (int i = 0; i < binaryString.length; i++) {
        totalValue += (int)([binaryString characterAtIndex:(binaryString.length - 1 - i)] - 48) * 10;
    }
    return @(totalValue);
}


-(NSNumber *) hexToNumber:(NSString *) msg {
    unsigned result = 0;
    NSScanner *scanner = [NSScanner scannerWithString:msg];
    [scanner scanHexInt:&result];
    return [NSNumber numberWithInt:result];
}

-(BlePeripheral *) parseValueString:(NSString *) msg: (CBPeripheral *)cur_peripheral  RSSI:(NSNumber *)RSSI {
    if ([msg length] == 51) {
        msg = [self fixMsg:msg];
        NSString * manufacturerID = [msg substringWithRange:NSMakeRange(0, 4)];
        NSLog(manufacturerID);


        if ([manufacturerID isEqualToString:@"0849"]) {
    
            NSNumber * powerBladeID = [self hexToNumber:[msg substringWithRange:NSMakeRange(4, 2)]];
            NSNumber * sequence_num = [self hexToNumber:[msg substringWithRange:NSMakeRange(6, 8)]];
            NSNumber * pscale_exp = [self hexToNumber:[msg substringWithRange:NSMakeRange(14, 1)]];
            NSNumber * pscale_dem = [self hexToNumber:[msg substringWithRange:NSMakeRange(15, 3)]];
            NSNumber * vscale = [self hexToNumber:[msg substringWithRange:NSMakeRange(18, 2)]];
            NSNumber * whscale = [self hexToNumber:[msg substringWithRange:NSMakeRange(20, 2)]];
            NSNumber * v_rms = [self hexToNumber:[msg substringWithRange:NSMakeRange(22, 2)]];
            NSNumber * true_power = [self hexToNumber:[msg substringWithRange:NSMakeRange(24, 4)]];
            NSNumber * apparent_power = [self hexToNumber:[msg substringWithRange:NSMakeRange(28, 4)]];
            NSNumber * watt_hours = [self hexToNumber:[msg substringWithRange:NSMakeRange(32, 8)]];
            NSNumber * flags = [self hexToNumber:[msg substringWithRange:NSMakeRange(40, 2)]];


            NSNumber *volt_scale = [NSNumber numberWithFloat:[vscale floatValue]/50];
            NSLog(@"volt_scale: %f", [volt_scale floatValue]);
            NSLog(@"seq num: %f", [sequence_num floatValue]);
            float pscale_dem_float = [pscale_dem floatValue];
            float pscale_exp_float = [pscale_exp floatValue];
            float pscale_exp_done = pow(10,-1*pscale_exp_float);
            float final_pscale = pscale_dem_float * pscale_exp_done;
            NSNumber * power_scale = [NSNumber numberWithFloat:final_pscale];
            NSLog(@"power scale: %f", [power_scale floatValue]);

            
            double vRMS_double = [v_rms doubleValue]*[volt_scale doubleValue];
            double tPower_double = [true_power doubleValue]*[power_scale doubleValue];
            double aPower_double = [apparent_power doubleValue]*[power_scale doubleValue];
            double wHr_double = 0;
            if(volt_scale > 0) {
                 //scale for power * 2^(exponent) / 3600
                double wh_exp = pow(2, [whscale doubleValue]) / 3600;
                wHr_double = wh_exp*[power_scale doubleValue]*[watt_hours doubleValue];
            }
            else {
                wHr_double = [watt_hours doubleValue];
            }
            double pFactor = tPower_double / aPower_double;

            //NSNumber * wh_scale = [[NSNumber numberWithFloat:[pow(2,[whscale doubleValue])/3600]] ];
            //NSLog(@"wh_scale: %d", wh_scale);
            
            NSDateFormatter *timeFormatter = [[NSDateFormatter alloc] init];
            [timeFormatter setDateFormat:@"MM/dd/yyyy HH:mm:ss"];
            [timeFormatter setTimeZone:[NSTimeZone timeZoneWithName:@"GMT"]];
            NSString * newTime = [timeFormatter stringFromDate:[[NSDate alloc]init]];
            
            BlePeripheral *l_per = [[BlePeripheral alloc]init];
            l_per.m_powerBladeID = [powerBladeID integerValue];
            l_per.m_sequenceNum = [sequence_num integerValue];
            l_per.m_time = [newTime longLongValue];
            l_per.m_vRMS = vRMS_double;
            l_per.m_tPower = tPower_double;
            l_per.m_aPower = aPower_double;
            l_per.m_wHr = wHr_double;
            l_per.m_rssi = [RSSI doubleValue];
            l_per.m_flags = [NSString stringWithFormat:@"%f", [flags doubleValue]];
            l_per.m_pfactor = pFactor;
            l_per.last_time = newTime;
            [last_seen setObject:newTime forKey:[NSNumber numberWithInt:l_per.m_powerBladeID]];
            return l_per;

            
        }
        

    }
    return NULL;
}


- (void)centralManager:(CBCentralManager *)central didConnectPeripheral:(CBPeripheral *)peripheral;
{
    [m_manger stopScan];
    m_peripheral = peripheral;
    m_peripheral.delegate = self;
    [mange_delegate bleMangerConnectedPeripheral:YES];
    [m_peripheral discoverServices:nil];
}

- (void)centralManager:(CBCentralManager *)central didDisconnectPeripheral:(CBPeripheral *)peripheral error:(NSError *)error;
{
    [mange_delegate bleMangerDisconnectedPeripheral:peripheral];
}
- (void)peripheral:(CBPeripheral *)peripheral didDiscoverServices:(NSError *)error;
{
    for (CBService *s in [peripheral services]) {
        [peripheral discoverCharacteristics:nil forService:s];
    }
}
- (void)peripheral:(CBPeripheral *)peripheral didUpdateValueForCharacteristic:(CBCharacteristic *)characteristic error:(NSError *)error;
{
    [mange_delegate bleMangerReceiveDataPeripheralData:characteristic.value from_Characteristic:characteristic];
}
-(BOOL) isPeripheralEqual :(CBPeripheral *)cur_peripheral RSSI:(NSNumber *)RSSI
{
    if ([m_array_peripheral count]>0) {
        for (int i=0;i<[m_array_peripheral count];i++) {
            BlePeripheral *l_per = [m_array_peripheral objectAtIndex:i];
            if ([cur_peripheral isEqual:l_per.m_peripheral]) {
                return YES;
            }
        }
    }
    return NO;
}

@end
