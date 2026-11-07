# Retinal Image Lab

Open **Signal lab → Retinal Image Lab** on the laptop or on a paired phone. The laptop runs the algorithm and sends the preview to the requesting device.

## Connect and process

1. Keep Orbit open on the laptop. Put both devices on the same trusted Wi-Fi or use the laptop hotspot.
2. In **Connect**, select the address for that network and create a phone QR. Scan it and choose **Continue in this browser** or open it with APK 4.1. A fresh QR is required after a previous token has been used.
3. Choose a fundus JPEG or PNG and confirm permission for local processing. The source may come from appropriate imaging equipment or a dataset whose license permits this use.
4. Choose **Process preview**. Inspect Input, Enhanced, Vessel response, Binary mask and Overlay. Processing settings control scale, morphological radius, component size and threshold sensitivity.
5. Choose **Process & save to Library** to keep the original and derived images in the existing Lab notebook. Saved entries can be reopened from either device. Permanent deletion is available from the laptop and checks for dependent results before deleting an original.

The current file limits are 8 MiB, 16 megapixels at source, and at most 1,024 pixels on the processed image's longest side. Python is the default engine. MATLAB requires an installed license with Image Processing Toolbox. Its startup time is included in the measured run duration. Each engine uses its own CLAHE and adaptive-threshold defaults.

The phone uses the laptop's CPU and storage. The current experiment processes uploaded still images. Continuous retinal video would require compatible retinal imaging equipment, a working capture interface and measured throughput on that setup. Ordinary webcam eye images do not supply a fundus view.

## Algorithm and interpretation

Python uses a green-channel image, CLAHE, median filtering, morphological black-hat enhancement, adaptive thresholding, opening and connected-component cleanup. The field mask excludes most of the dark border. Binary foreground pixels are **vessel candidates** produced by these image operations.

The MATLAB script uses imread, rgb2gray, adapthisteq, medfilt2, imbothat, imbinarize, imopen and component cleanup. Save the image as input.png beside the downloaded script to run the default example manually.

This is an educational image-processing experiment. It has no clinical validation, diagnosis or blood-pressure measurement. Source type is explicitly declared as an uploaded fundus photo or a generated test image. No accuracy or Dice value is reported without reference annotations.

## Data handling

Preview requests are processed in memory. MATLAB also uses a temporary job folder that is removed after completion. **Save** stores files in the authenticated laptop media library. The local server uses the project's existing trusted-LAN HTTP transport. Use consented, appropriately de-identified research images on a trusted network.

## References

- [MathWorks CLAHE documentation](https://www.mathworks.com/help/images/ref/adapthisteq.html)
- [MathWorks adaptive binarization documentation](https://www.mathworks.com/help/images/ref/imbinarize.html)
- [MathWorks bottom-hat filtering documentation](https://www.mathworks.com/help/images/ref/imbothat.html)
- [Ophthalmic Photographers' Society fundus photography overview](https://www.opsweb.org/page/fundusphotography)
