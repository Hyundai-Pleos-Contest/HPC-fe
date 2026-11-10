package com.hpc.app

import android.os.Handler
import android.os.Looper
import android.os.SystemClock
import android.util.Log
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import ai.pleos.playground.vehicle.Vehicle
import ai.pleos.playground.vehicle.api.model.area.DoorArea
import ai.pleos.playground.vehicle.constant.area.DoorValue
import java.util.concurrent.Semaphore
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicReference
import org.junit.Assert.fail
import org.junit.Test
import org.junit.runner.RunWith

/** Read-only environment check for the dedicated Pleos AVD; no vehicle controls. */
@RunWith(AndroidJUnit4::class)
class VehicleSdkSmokeTest {
    @Test
    fun receivesDoorPositionFromVehicleService() {
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        lateinit var vehicle: Vehicle
        instrumentation.runOnMainSync {
            vehicle = Vehicle(instrumentation.targetContext.applicationContext)
        }
        val closed = AtomicBoolean(false)

        try {
            instrumentation.runOnMainSync { vehicle.initialize() }
            val door = vehicle.getDoor()
            val area = DoorArea(DoorValue.ROW_1_LEFT)
            val deadline = SystemClock.elapsedRealtime() + 30_000
            val mainHandler = Handler(Looper.getMainLooper())
            val position = AtomicReference<Int?>()
            val lastFailure = AtomicReference("Vehicle Service has not returned a callback.")
            val callback = Semaphore(0)
            fun failure(message: String) {
                if (!closed.get()) {
                    lastFailure.set(message)
                    callback.release()
                }
            }
            fun failure(exception: Exception) {
                failure("${exception.javaClass.simpleName}: ${exception.message}")
            }

            // initialize() starts an asynchronous bind. Only a capability and data callback
            // from the service count as success, never the return of initialize() itself.
            while (SystemClock.elapsedRealtime() < deadline && position.get() == null) {
                instrumentation.runOnMainSync {
                    try {
                        door.checkDoorPositionCapabilities(
                            onComplete = { config, bounds ->
                                // Serialize new reads with release(), even if a capability
                                // callback arrives late on a Binder thread.
                                mainHandler.post {
                                    if (!closed.get() && position.get() == null && SystemClock.elapsedRealtime() < deadline) {
                                        if (!bounds.containsKey(area)) {
                                            failure("ROW_1_LEFT is unavailable; access=${config.accessType}.")
                                        } else {
                                            try {
                                                door.getCurrentDoorPosition(
                                                    area = area,
                                                    onComplete = { value ->
                                                        if (!closed.get() && SystemClock.elapsedRealtime() <= deadline) {
                                                            if (value == null) {
                                                                failure("Door callback returned null.")
                                                            } else {
                                                                // Preserve success from any attempt; a later
                                                                // retry failure cannot replace a real value.
                                                                position.set(value)
                                                                callback.release()
                                                            }
                                                        }
                                                    },
                                                    onFailed = ::failure,
                                                )
                                            } catch (exception: Exception) {
                                                failure(exception)
                                            }
                                        }
                                    }
                                }
                            },
                            onFailed = ::failure,
                        )
                    } catch (exception: Exception) {
                        failure(exception)
                    }
                }

                val remaining = (deadline - SystemClock.elapsedRealtime()).coerceAtLeast(0)
                if (!callback.tryAcquire(minOf(5_000, remaining), TimeUnit.MILLISECONDS)) {
                    lastFailure.set("No callback within the attempt timeout.")
                }
                if (position.get() == null) {
                    SystemClock.sleep(minOf(250, (deadline - SystemClock.elapsedRealtime()).coerceAtLeast(0)))
                }
            }

            val receivedPosition = position.get()
            if (receivedPosition == null) {
                fail("Pleos Vehicle SDK did not return a readable door value within 30 seconds. Last result: ${lastFailure.get()}")
            }
            Log.i("HpcPleosSmoke", "Vehicle Service capability and door read callbacks received; position=$receivedPosition")
        } finally {
            closed.set(true)
            instrumentation.runOnMainSync { vehicle.release() }
        }
    }
}
