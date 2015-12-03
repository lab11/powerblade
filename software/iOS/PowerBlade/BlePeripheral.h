#import <Foundation/Foundation.h>
#import <CoreBluetooth/CoreBluetooth.h>
@interface BlePeripheral : NSObject
@property(nonatomic,copy)CBPeripheral *m_peripheral;
@property(nonatomic)     NSInteger  m_powerBladeID;
@property(nonatomic)     NSInteger  m_sequenceNum;
@property(nonatomic)     NSInteger  m_time;
@property(nonatomic)     double  m_pfactor;

@property(nonatomic) NSString * last_time;

@property(nonatomic)     double  m_rssi;

@property(nonatomic)     double  m_vRMS;
@property(nonatomic)     double  m_tPower;
@property(nonatomic)     double  m_aPower;
@property(nonatomic)     double  m_wHr;
@property(nonatomic, copy)  NSString * m_flags;
@property(nonatomic, copy)  NSString * m_adr;
@property(nonatomic)  NSInteger m_numConnections;

@end



