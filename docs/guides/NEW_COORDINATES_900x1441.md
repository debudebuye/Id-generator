# New Coordinate Reference: 900x1441px

## Overview
Updated reference dimensions from 591x1280px to 900x1441px for better accuracy and higher resolution extraction.

## Reference Image Dimensions
- **Width:** 900px
- **Height:** 1441px
- **Aspect Ratio:** 0.6245 (900/1441)

## Coordinate Status

### ✅ Updated Coordinates

#### Full Name (Amharic)
- **X:** 89px
- **Y:** 834px
- **Width:** 703px
- **Height:** 51px
- **Region:** (89, 834) to (792, 885)
- **Status:** ✅ Updated

### ⏳ Pending Coordinates (Need User Input)

Please provide the following coordinates in the same format (X, Y, W, H):

#### Full Name (English)
- **Current (scaled from old):** Using old reference
- **Status:** ⏳ Needs update
- **Format needed:** X: ?, Y: ?, W: ?, H: ?

#### Date of Birth (Ethiopian)
- **Current (scaled from old):** Using old reference
- **Status:** ⏳ Needs update
- **Format needed:** X: ?, Y: ?, W: ?, H: ?

#### Date of Birth (Gregorian)
- **Current (scaled from old):** Using old reference
- **Status:** ⏳ Needs update
- **Format needed:** X: ?, Y: ?, W: ?, H: ?

#### Sex (Amharic)
- **Current (scaled from old):** Using old reference
- **Status:** ⏳ Needs update
- **Format needed:** X: ?, Y: ?, W: ?, H: ?

#### Sex (English)
- **Current (scaled from old):** Using old reference
- **Status:** ⏳ Needs update
- **Format needed:** X: ?, Y: ?, W: ?, H: ?

#### Expiry Date (Ethiopian)
- **Current (scaled from old):** Using old reference
- **Status:** ⏳ Needs update
- **Format needed:** X: ?, Y: ?, W: ?, H: ?

#### Expiry Date (Gregorian)
- **Current (scaled from old):** Using old reference
- **Status:** ⏳ Needs update
- **Format needed:** X: ?, Y: ?, W: ?, H: ?

#### FAN Number
- **Current (scaled from old):** Using old reference
- **Status:** ⏳ Needs update
- **Format needed:** X: ?, Y: ?, W: ?, H: ?

#### Issue Date (Gregorian) - Vertical
- **Current (scaled from old):** Using old reference
- **Status:** ⏳ Needs update
- **Format needed:** X: ?, Y: ?, W: ?, H: ?

#### Issue Date (Ethiopian) - Vertical
- **Current (scaled from old):** Using old reference
- **Status:** ⏳ Needs update
- **Format needed:** X: ?, Y: ?, W: ?, H: ?

## How to Provide Coordinates

Use Adobe Photoshop, GIMP, or any image editor to measure:

1. Open the 900x1441px front ID card image
2. Use the selection tool to select each field region
3. Note down X, Y, W, H values
4. Provide in this format:

```
Field Name: X: 89, Y: 834, W: 703, H: 51
```

## Comparison: Old vs New Reference

| Aspect | Old Reference | New Reference | Change |
|--------|--------------|---------------|--------|
| Width | 591px | 900px | +52% |
| Height | 1280px | 1441px | +13% |
| Aspect Ratio | 0.4617 | 0.6245 | +35% |
| Total Pixels | 756,480 | 1,296,900 | +71% |

## Benefits of New Reference

1. **Higher Resolution:** 71% more pixels for better OCR accuracy
2. **Better Scaling:** Closer to actual ID card proportions
3. **Wider Coverage:** 703px width for names vs 405px (73% wider)
4. **Taller Regions:** 51px height vs 22px (132% taller)

## Testing

After all coordinates are updated, test with:

```bash
python tests/test_dimension_scaling.py
```

This will verify that the new coordinates scale properly for different image sizes.

## Notes

- The system will continue to work with old coordinates for fields not yet updated
- Old coordinates will be scaled from 591x1280 reference
- Once all coordinates are updated, extraction accuracy will improve significantly
- The percentage-based system ensures compatibility with any image size
