package edu.umich.eecs.lab11.powerblade;

import android.app.Service;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothManager;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.os.Handler;
import android.os.IBinder;
import android.preference.PreferenceManager;
import android.widget.Toast;

import java.text.DecimalFormat;
import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;

public class BleService extends Service {

    private boolean paused;
    private boolean mScanning;
    private Intent thisIntent;
    private Handler mScanHandler;
    private Integer radioSilenceCount = 0;
    private SharedPreferences cur_settings;
    private BluetoothManager mBluetoothManager;
    private BluetoothAdapter mBluetoothAdapter;
    private DecimalFormat di = new DecimalFormat("0");
    private DecimalFormat df = new DecimalFormat("0.##");

    // Pauses scanning after SCAN_PERIOD milliseconds, restarts 1 second later
    private final Integer SCAN_PERIOD = 10000;

    @Override
    public void onCreate() {
        super.onCreate();
        mScanHandler = new Handler();
        cur_settings = PreferenceManager.getDefaultSharedPreferences(this);
        if (!getPackageManager().hasSystemFeature(PackageManager.FEATURE_BLUETOOTH_LE)) {
            Toast.makeText(this, "BLE not supported", Toast.LENGTH_SHORT).show();
            stopSelf();
        }
        mBluetoothManager = (BluetoothManager) getSystemService(Context.BLUETOOTH_SERVICE);
        mBluetoothAdapter = mBluetoothManager.getAdapter();
        if (mBluetoothAdapter == null) {
            Toast.makeText(this, "Bluetooth not supported", Toast.LENGTH_SHORT).show();
            stopSelf();
        }
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (!mBluetoothAdapter.isEnabled()) {
            try {
                mBluetoothAdapter.enable();
            } catch (Exception e) {
                Intent enableBtIntent = new Intent(BluetoothAdapter.ACTION_REQUEST_ENABLE);
                enableBtIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                getBaseContext().startActivity(enableBtIntent);
            }
        }
        paused = false;
        thisIntent = intent;
        scanLeDevice(true); // Start BLE Scan
        return super.onStartCommand(intent, flags, startId);
    }

    @Override
    public void onDestroy() {
        paused = true;
        mScanning = false;
        mBluetoothAdapter.stopLeScan(mLeScanCallback); // Stop BLE Scan
        super.onDestroy();
    }

    private void scanLeDevice(final boolean enable) {
        if (enable & !paused & !mScanning) {
            mScanHandler.postDelayed(new Runnable() { @Override public void run() { scanLeDevice(false); } }, SCAN_PERIOD);
            try { mScanning = mBluetoothAdapter.startLeScan(mLeScanCallback); } catch (Exception e) { e.printStackTrace(); }
        } else {
            if (!paused) {
                if (radioSilenceCount++ > 5) { // No devices detected for 1 min, restart service to be safe
                    mScanHandler.postDelayed(new Runnable() {
                        @Override
                        public void run() {
                            startService(thisIntent);
                            scanLeDevice(true);
                        }
                    }, 5000);
                    System.out.println("PERIPHERALS ARE NOT BEING SCANNED. RESTARTING SERVICE.");
                    mBluetoothAdapter.disable();
                    stopSelf();
                } else mScanHandler.postDelayed(new Runnable() { @Override public void run() { scanLeDevice(true); } }, 1000);
            }
            try {
                mBluetoothAdapter.stopLeScan(mLeScanCallback);
                mScanning = false;
            } catch (Exception e) { e.printStackTrace(); }

        }
    }

    private BluetoothAdapter.LeScanCallback mLeScanCallback = new BluetoothAdapter.LeScanCallback() {
        @Override
        public void onLeScan(final BluetoothDevice device, final int rssi, final byte[] scanRecord) {
            try {
                radioSilenceCount=0;
                //System.out.println(device.getName() + " : " + getHexString(scanRecord));
                parseStuff(device, rssi, scanRecord);
            } catch (Exception e) { e.printStackTrace(); }
        }
    };

    @Override
    public IBinder onBind(Intent intent) { return null; }

    public double fixData(String msg) {
        Map<String, String> m = new HashMap<String, String>();
        m.put("0","0000");
        m.put("1","0001");
        m.put("2","0010");
        m.put("3","0011");
        m.put("4","0100");
        m.put("5","0101");
        m.put("6","0110");
        m.put("7","0111");
        m.put("8","1000");
        m.put("9","1001");
        m.put("A","1010");
        m.put("B","1011");
        m.put("C","1100");
        m.put("D","1101");
        m.put("E","1110");
        m.put("F", "1111");
        System.out.println(msg);
        String bits = "";
        for (int i = 0 ; i < msg.length(); i++) {
            bits += m.get(String.valueOf(msg.charAt(i)));
        }
        System.out.println(bits);
        String reversedbits = "";
        int index = bits.length();
        while (index > 0) {
            index--;
            reversedbits += bits.substring(index, index+1);
        }
        System.out.println(reversedbits);
        return Double.valueOf(Integer.parseInt(reversedbits,2));

    }

    public void parseStuff(BluetoothDevice device, int rssi, byte[] scanRecord) {
        int index = 0;
        while (index < scanRecord.length) {
            int length = scanRecord[index++];
            if (length == 0) break; // Done once we run out of records
            int type = scanRecord[index];
            if (type == 0) break; // Done if our record isn't a valid type
            if (type==-1 && scanRecord[index+1]==0x08 && scanRecord[index+2]==0x49) {
                //System.out.println("Type matched, Parsing : " + device.getAddress());
                byte[] data = Arrays.copyOfRange(scanRecord, index + 3, index + length);

                //because I am completely sick of dealing with this and am hitting bullshit
                //over and over again, we will be quick about it and use... strings... thats right
                StringBuilder sb = new StringBuilder();
                for (byte b : data) {
                    sb.append(String.format("%02X ", b));
                }
                String bytes = sb.toString().replaceAll("\\s+","");
                double pbid = fixData(bytes.substring(0, 2));
                double sequenceNum = fixData(bytes.substring(2, 10));
                double time = fixData(bytes.substring(10,18));
                double vrms = fixData(bytes.substring(18, 20))*2.460;
                double trup = fixData(bytes.substring(20,24))*0.058;
                double appp = fixData(bytes.substring(24,28))*0.058;
                double wthr = fixData(bytes.substring(28, 36))*0.0000161;
                double flags = fixData(bytes.substring(36, 38));
                double numCmd = fixData(bytes.substring(38, 40));
                double pwfr = (trup / appp) * 1.0000000;
                cur_settings.edit().putString("address",      device.getAddress()).apply();
                cur_settings.edit().putString("id",             di.format( pbid )).apply();
                cur_settings.edit().putString("power",          di.format( trup )).apply();
                cur_settings.edit().putString("v_rms",          df.format( vrms )).apply();
                cur_settings.edit().putString("true_power",     df.format( trup )).apply();
                cur_settings.edit().putString("apparent_power", df.format( appp )).apply();
                cur_settings.edit().putString("watt_hours",     df.format( wthr )).apply();
                cur_settings.edit().putString("power_factor",   df.format( pwfr )).apply();
                cur_settings.edit().putLong  ("time",  System.currentTimeMillis()).apply();
            }
            index += length; // Advance
        }
    }

}
