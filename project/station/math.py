import cv2
import numpy as np


def largest_rectangle(contour):
    x, y, w, h = cv2.boundingRect(contour)
    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.drawContours(mask,
                     [contour - (x, y)],
                     0,
                     (255.0, 0.0, 0.0),
                     -1)

    height = np.zeros((h, w), dtype=int)

    for j in range(w):
        for i in range(h):
            if mask[i, j] == 255:
                height[i, j] = 1 + height[i - 1, j] if i > 0 else 1
            else:
                height[i, j] = 0

    max_area = 0
    best_rect = None

    for i in range(h):
        stack = []
        for j in range(w + 1):
            if j < w:
                h = height[i, j]
            else:
                h = 0

            start = j

            while stack and stack[-1][1] > h:
                j_prev, h_prev = stack.pop()
                area = (j - j_prev) * h_prev
                if area > max_area:
                    max_area = area
                    best_rect = (j_prev, i - h_prev + 1, j - j_prev - 3, h_prev - 3)
                start = j_prev
            stack.append((start, h))

    if best_rect is not None:
        i, j, w, h = best_rect
        box = np.array([
            [i, j],
            [i + w, j],
            [i + w, j + h],
            [i, j + h]
        ],
            dtype=np.int32)

        box += (x, y)

        return box, max_area

    else:
        return None, 0


def bounding_rectangular(y_max_global, y_min_global, segment, frame):
    x_min, y_min, width, height = cv2.boundingRect(np.array(segment))

    y_min_global = min(y_min_global, y_min)
    y_max_global = max(y_max_global, y_min + height)

    distance_y = (y_max_global - y_min_global - 1)

    box = np.array([[x_min, y_min],
                    [x_min + width - 1, y_min],
                    [x_min + width - 1, y_min + height - 1],
                    [x_min, y_min + height - 1]])

    if distance_y > 0:
        segment = segment.astype(int)

        cv2.polylines(frame,
                      [box],
                      isClosed=True,
                      color=(255, 0, 0),
                      thickness=2
                      )
        cv2.polylines(frame,
                      [segment],
                      isClosed=True,
                      color=(0, 0, 255),
                      thickness=2
                      )

    return distance_y


def text_placement(moment, draw_area, area, frame):
    if moment["m00"] != 0:
        c_x = int(moment["m10"] / moment["m00"])
        c_y = int(moment["m01"] / moment["m00"])

        if draw_area:
            text_size = 0.3
            text_color = (0, 0, 255)
            text = f"{int(area)}"
            text_size_tuple = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, text_size, 1)[0]
            text_x = c_x - text_size_tuple[0] // 2
            text_y = c_y + text_size_tuple[1] // 2
            cv2.putText(frame, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, text_size, text_color, 1)


def contour_edge_distances(segment, frame=None, draw=True, color=(0, 255, 0)):

    x_min = int(np.min(segment[:, 0]))
    x_max = int(np.max(segment[:, 0]))
    y_min = int(np.min(segment[:, 1]))

    theoretical_x_mid = (x_min + x_max) / 2
    left_points = segment[segment[:, 0] <= theoretical_x_mid]
    right_points = segment[segment[:, 0] >= theoretical_x_mid]

    near_points = np.concatenate([left_points,right_points], axis=0)

    x_md = int(max(np.max(left_points[:,0]), np.min(right_points[:,0])))
    x_mid = int(theoretical_x_mid)
    nears = segment[(segment[:,0] >= x_mid - 10) & (segment[:,0] <= x_mid + 10) & (segment[:,1] > y_min + 3)]
    if nears.size == 0:
        y_mid = int(np.min(segment[segment[:, 0] == x_md]))
        nears = np.vstack([nears, [x_md, y_mid]])
    y_mid = int(np.min(nears[:,1]))

    height = y_mid - y_min

    # отладка контура
    # if draw and frame is not None:
        # cv2.line(frame, (x_mid, y_min),(x_mid, y_min), (255, 255, 255), 10, cv2.LINE_AA)
        # cv2.line(frame, (x_mid, y_mid), (x_mid, y_mid), (0, 0, 255), 10, cv2.LINE_AA)
        # cv2.polylines(frame, [segment], isClosed=True, color=color, thickness=2)

    return height, [x_mid, y_min,y_mid]