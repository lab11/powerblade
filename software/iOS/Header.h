//
//  Header.h
//  BLE4.0Demo
//
//  Created by kakaxi on 15/4/24.
//  Copyright (c) 2015年 szvson. All rights reserved.
//

#ifndef BLE4_0Demo_Header_h
#define BLE4_0Demo_Header_h


#define MainScreen_Width   [[UIScreen mainScreen]bounds].size.width
#define MainScreen_Height  [[UIScreen mainScreen]bounds].size.height
//单例
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




#endif
