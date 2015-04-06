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

import java.nio.ByteBuffer;
import java.text.DecimalFormat;
import java.util.Arrays;

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
                System.out.println(device.getName() + " : " + getHexString(scanRecord));
                parseStuff(device, rssi, scanRecord);
            } catch (Exception e) { e.printStackTrace(); }
        }
    };

    @Override
    public IBinder onBind(Intent intent) { return null; }

    public static String getHexString(byte[] buf) {
        if (buf != null) {
            StringBuilder sb = new StringBuilder();
            for (byte b : buf) sb.append(String.format("%02X", b));
            return sb.toString();
        } else return "";
    }

    public void parseStuff(BluetoothDevice device, int rssi, byte[] scanRecord) {
        int index = 0;
        while (index < scanRecord.length) {
            int length = scanRecord[index++];
            if (length == 0) break; // Done once we run out of records
            int type = scanRecord[index];
            if (type == 0) break; // Done if our record isn't a valid type
            if (type==-1 && scanRecord[index+1]==0x08 && scanRecord[index+2]==0x49) {
                System.out.println("Type matched, Parsing : " + device.getAddress());
                byte[] data = Arrays.copyOfRange(scanRecord, index + 3, index + length);
                double pbid = 1.0000000 * (data[0] & 0xff);
                double vrms = 2.4600000 * (data[9] & 0xff);
                double trup = 0.0150000 * (ByteBuffer.wrap(Arrays.copyOfRange(data,10,12)).getShort() & 0xffff);
                double appp = 0.0150000 * (ByteBuffer.wrap(Arrays.copyOfRange(data,12,14)).getShort() & 0xffff);
                double wthr = 0.0000057 * (ByteBuffer.wrap(Arrays.copyOfRange(data,14,18)).getInt() & 0xffffffffL);
                double pwfr = 1.0000000 * (trup / appp);
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
